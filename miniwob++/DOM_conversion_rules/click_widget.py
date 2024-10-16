from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = convert_df_base_formatting(df)

    # replace 't' with 'text'
    df = df.replace('t', 'text')

    return df
