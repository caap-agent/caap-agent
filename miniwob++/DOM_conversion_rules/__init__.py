import pandas as pd


# replace 'tag' values.
# rename the 'tag' column to 'type'
# add xy & delete left, width, top, height
# replace 'focused' values.
# replace 'checked' values.
# insert value string to text, if text string is None
def convert_df_base_formatting(df: pd.DataFrame) -> pd.DataFrame:
    df = convert_df_coords_format(df)
    df = convert_df_text_format(df)
    df = convert_df_focused_format(df)
    df = convert_df_checked_format(df)
    df = convert_df_type_format(df)
    return df


def convert_df_type_format(df: pd.DataFrame) -> pd.DataFrame:
    # replace tag values.
    rename_tags = {'input_checkbox': 'checkbox',
                   'input_text': 'input_field',
                   'input_radio': 'radio',
                   'input_password': 'input_field',
                   'input_number': 'input_field',
                   'label': 'text',
                   'select': 'dropdown',
                   'textarea': 'text_area'}
    for tag_from, tag_to in rename_tags.items():
        df.loc[df['tag'] == tag_from, 'tag'] = tag_to

    # rename the 'tag' column to 'type'
    if 'tag' in df.columns:
        df = df.rename(columns={'tag': 'type'})
    return df

def convert_df_coords_format(df: pd.DataFrame) -> pd.DataFrame:
    # add xy & delete left, width, top, height
    if all([col in df.columns for col in ['left', 'width', 'top', 'height']]):
        df['x1'] = round(df['left']).astype(int)
        df['x2'] = round(df['left'] + df['width']).astype(int)
        df.drop(['left', 'width'], axis=1, inplace=True)
        df['y1'] = round(df['top']).astype(int)
        df['y2'] = round(df['top'] + df['height']).astype(int)
        df.drop(['top', 'height'], axis=1, inplace=True)
    return df


def convert_df_focused_format(df: pd.DataFrame) -> pd.DataFrame:
    # replace 0 with empty string in 'bool' column
    if 'focused' in df.columns:
        df['focused'] = df['focused'].replace(0, 'False')
        df['focused'] = df['focused'].replace(1, 'True')
    return df


def convert_df_checked_format(df: pd.DataFrame) -> pd.DataFrame:
    if 'checked' in df.columns:
        df['checked'] = 'False'
        target_types = ['input_checkbox', 'input_radio']
        # replace 0 with empty string in 'bool' column
        for t in target_types:
            df.loc[(df['value'] == 'True') & (df['type'] == t), 'checked'] = 'True'
    return df


def convert_df_text_format(df: pd.DataFrame) -> pd.DataFrame:
    # insert value string to text, if text string is None
    if all([col in df.columns for col in ['text', 'value']]):
        df.loc[(df['text'].str.len() == 0) & (df['value'].str.len() > 0), 'text'] = df['value']
    return df
