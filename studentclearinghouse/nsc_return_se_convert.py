import pandas as pd

#' Convert National Student Clearinghouse return file to database format
#'
#' Convert the National Student Clearinghouse return file to a database format
#' that is easier to work with. Each student will have one record per college
#' attended. Additional records are added for each degree earned. If a student
#' did not attend a college that reports to the NSC, then Record Found Y/N will
#' be 'N'.
#'
#' @param fn Full path to the details file provided by NSC
#' @keywords file
#' @export
#' @importFrom pandas read_csv concat merge to_datetime dropna fillna groupby transform cumcount sort_values
#'
def nsc_return_se_convert(fn):

    # Load the specified file, fn, into a pandas dataframe
    students = pd.read_csv(fn, dtype=str)

    # Replace NAs in Middle Initial and Name Suffix with blanks
    students['Middle Initial'] = students['Middle Initial'].fillna('')
    students['Name Suffix'] = students['Name Suffix'].fillna('')

    # get students with no activity into no_act
    no_act = students[students['Record Found Y/N'] == 'N']
    # Keep the columns from `Your Unique Identifier` through `Search Date` in no_act
    # The other columns will be adding in later
    no_act = no_act.loc[:, 'Your Unique Identifier':'Search Date']

    # In students, keep only the records that were found
    students = students[students['Record Found Y/N'] == 'Y']
    # Convert the dates into dates
    students['Enrollment Begin'] = pd.to_datetime(students['Enrollment Begin'], format='%Y%m%d')
    students['Enrollment End'] = pd.to_datetime(students['Enrollment End'], format='%Y%m%d')

    students['Enrollment Days'] = students['Enrollment End'] - students['Enrollment Begin']

    # Calculate the days between Enrollment Begin and Enrollment End and store as an integer
    students['Enrollment Days'] = students['Enrollment Days'].dt.days

    # Replace NAs in Enrollment Major 2 and Enrollment CIP 2 with blanks
    students['Enrollment Major 2'] = students['Enrollment Major 2'].fillna('')
    students['Enrollment CIP 2'] = students['Enrollment CIP 2'].fillna('')
    
    # Fix the graduation records
    # Keep only the graduated records
    graduated = students[students['Graduated?'] == 'Y']
    # Keep only the columns we want
    graduated = graduated.loc[:, ['Last Name', 'First Name', 'Middle Initial', 'Name Suffix', 'College Sequence',
                                    'Graduated?', 'Graduation Date', 'Degree Title',
                                    'Degree Major 1', 'Degree CIP 1',
                                    'Degree Major 2', 'Degree CIP 2',
                                    'Degree Major 3', 'Degree CIP 3',
                                    'Degree Major 4', 'Degree CIP 4']]
    # Fix the NA values
    graduated['Degree Title'] = graduated['Degree Title'].fillna('UNKNOWN')
    graduated['Degree Major 1'] = graduated['Degree Major 1'].fillna('UNKNOWN')
    graduated['Degree CIP 1'] = graduated['Degree CIP 1'].fillna('UNKNOWN')


    # Remove graduation records as they were handled above
    students = students[students['Graduated?'] == 'N']
    # Remove graduation columns - they will be added back later
    students = students.drop(['Graduated?', 'Graduation Date', 'Degree Title',
                                'Degree Major 1', 'Degree CIP 1',
                                'Degree Major 2', 'Degree CIP 2',
                                'Degree Major 3', 'Degree CIP 3',
                                'Degree Major 4', 'Degree CIP 4'], axis=1)
    # Add a row index
    students['RowNumber'] = students.index
    # We need to fill down the CollegeSequence value since it is missing for
    #    subsequent records
    students['College Sequence'] = students.groupby(['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                                                    'Requester Return Field', 'Enrollment Begin'])['College Sequence'].ffill()

    # Now regroup so we can add the number of Semesters at Institution,
    #     keeping one row with earliest Begin date and the latest End date
    students['Semesters at Institution'] = students.groupby(['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                                                    'Requester Return Field', 'College Sequence'])['Enrollment Begin'].transform('count')
    students['SemesterIndex'] = students.groupby(['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                                                    'Requester Return Field', 'College Sequence'])['Enrollment Begin'].cumcount() + 1
    students['Enrollment Begin'] = students.groupby(['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                                                    'Requester Return Field', 'College Sequence'])['Enrollment Begin'].transform('min')
    students['Enrollment End'] = students.groupby(['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                                                    'Requester Return Field', 'College Sequence'])['Enrollment End'].transform('max')
    students['Total Enrollment Days'] = students.groupby(['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                                                    'Requester Return Field', 'College Sequence'])['Enrollment Days'].transform('sum')
    students['Last Enrollment Major 1'] = students.groupby(['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                                                    'Requester Return Field', 'College Sequence'])['Enrollment Major 1'].transform('last')
    students['Last Enrollment CIP 1'] = students.groupby(['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                                                    'Requester Return Field', 'College Sequence'])['Enrollment CIP 1'].transform('last')
    students['Last Enrollment Major 2'] = students.groupby(['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                                                    'Requester Return Field', 'College Sequence'])['Enrollment Major 2'].transform('last')
    students['Last Enrollment CIP 2'] = students.groupby(['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                                                    'Requester Return Field', 'College Sequence'])['Enrollment CIP 2'].transform('last')
    students = students[students['SemesterIndex'] == 1]
    # Drop the RowNumber variable as it is no longer needed
    students = students.drop(['RowNumber', 'SemesterIndex'], axis=1)

    # Bring students with no activity back into the data frame
    students = pd.concat([students, no_act])
    # Bring in graduation data
    students = pd.merge(students, graduated, how='left', on=['Last Name', 'First Name', 'Middle Initial', 'Name Suffix', 'College Sequence'])
    # Any records where Graduated is NA should be set to 'N'
    students['Graduated?'] = students['Graduated?'].fillna('N')
    # students['Graduation Date'] = students['Graduation Date'].fillna('UNKNOWN')
    # students['Degree Title'] = students['Degree Title'].fillna('UNKNOWN')
    # students['Degree Major 1'] = students['Degree Major 1'].fillna('UNKNOWN')
    # students['Degree CIP 1'] = students['Degree CIP 1'].fillna('UNKNOWN')
    # students['Degree Major 2'] = students['Degree Major 2'].fillna('UNKNOWN')
    # students['Degree CIP 2'] = students['Degree CIP 2'].fillna('UNKNOWN')
    # students['Degree Major 3'] = students['Degree Major 3'].fillna('UNKNOWN')
    # students['Degree CIP 3'] = students['Degree CIP 3'].fillna('UNKNOWN')
    # students['Degree Major 4'] = students['Degree Major 4'].fillna('UNKNOWN')
    # students['Degree CIP 4'] = students['Degree CIP 4'].fillna('UNKNOWN')

    # Sort the data frame
    students = students.sort_values(['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                                    'Requester Return Field', 'College Sequence'])
    # Keep only the columns we want
    students = students[['Last Name', 'First Name', 'Middle Initial', 'Name Suffix',
                        'Requester Return Field', 'Record Found Y/N', 'Search Date',
                        'College Sequence', 'College Code/Branch', 'College Name', 'College State',
                        '2-year / 4-year', 'Public / Private',
                        'Enrollment Begin', 'Enrollment End', 'Enrollment Status', 'Class Level',
                        'Enrollment Major 1', 'Enrollment CIP 1',
                        'Enrollment Major 2', 'Enrollment CIP 2',
                        'Last Enrollment Major 1', 'Last Enrollment CIP 1',
                        'Last Enrollment Major 2', 'Last Enrollment CIP 2',
                        'Semesters at Institution', 'Total Enrollment Days',
                        'Graduated?', 'Graduation Date', 'Degree Title',
                        'Degree Major 1', 'Degree CIP 1',
                        'Degree Major 2', 'Degree CIP 2',
                        'Degree Major 3', 'Degree CIP 3',
                        'Degree Major 4', 'Degree CIP 4']]
    
    # Replace NAs with 0 for College Sequence
    students['College Sequence'] = students['College Sequence'].fillna(0)
    students['Semesters at Institution'] = students['Semesters at Institution'].fillna(0)
    students['Total Enrollment Days'] = students['Total Enrollment Days'].fillna(0)

    # Return the students dataframe
    return students.fillna('')

# For testing purposes only
if __name__ == "__main__":
    fn: str = "studentclearinghouse/999999st_123456_DETLRPT_SE_11012023000000_nsc_hcs_se_2022.csv"

    students = nsc_return_se_convert(fn)
                 
    print(students)
