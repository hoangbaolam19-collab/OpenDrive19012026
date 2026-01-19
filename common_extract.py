import pandas as pd


class CommonExtract:
    """
    A class to extract and process common junction data from navigation maps.
    
    This class provides functionality to identify merge and branch junctions
    based on one-way road data.
    """

    def __init__(self, file, path, flag):
        """
        Initialize the CommonExtract object.
        
        Args:
            file (str): The filename or identifier for the data.
            path (str): The path to the data directory.
            flag (int): Flag indicating junction type (0 for merge, non-zero for branch).
        """
        self.file = file
        self.path = path
        self.flag = flag

    def judge_junction(self, df_oneway, df_turnoff):
        """
        Determine merge and branch junctions based on one-way road data.
        
        Analyzes the relationship between start and end nodes to identify 
        merge junctions (1 start, 2 ends) or branch junctions (2 starts, 1 end).
        
        Args:
            df_oneway (DataFrame): DataFrame containing one-way road data with
                                  'snodeno' (start node) and 'enodeno' (end node) columns.
            df_turnoff (DataFrame): DataFrame containing turnoff data with 'nodeno' column.
        
        Returns:
            DataFrame: A DataFrame containing unique node numbers identified as
                      merge or branch junctions, depending on the flag value.
        """
        # Create empty DataFrame to store identification results
        df_turnoff_cut = df_turnoff.loc[:, "nodeno"].drop_duplicates().reset_index(drop=True)
        df_judge = pd.DataFrame(data={"nodeno": []})
        index_result = 0

        for i in range(len(df_turnoff_cut)):
            # Check how many start and end points the TURNOFF nodes have in ONE-WAY data
            df_bool = (df_oneway == df_turnoff_cut[i]).sum()

            # Save node numbers corresponding to merge or branch sections to DataFrame
            if self.flag == 0:
                # Merge sections have 1 start point and 2 end points
                if df_bool["snodeno"] == 1 and df_bool["enodeno"] == 2:
                    df_judge.loc[index_result] = df_turnoff_cut[i]
                    index_result += 1
            else:
                # Branch sections have 2 start points and 1 end point
                if df_bool["snodeno"] == 2 and df_bool["enodeno"] == 1:
                    df_judge.loc[index_result] = df_turnoff_cut[i]
                    index_result += 1

        # Return DataFrame with unique node numbers for merge (or branch) sections
        return df_judge



