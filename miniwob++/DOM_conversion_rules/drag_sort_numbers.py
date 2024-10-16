from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = convert_df_base_formatting(df)

    # replace 0 with empty string in 'bool' column
    df['focused'] = 'False'

    # convert type
    df = df.replace('div', 'unknown')
    df = df.replace('li', 'span')

    # data cleanning
    df = df[df['type'] != 'span']

    return df
