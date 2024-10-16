from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = convert_df_base_formatting(df)

    # replace 'div' with 'text'
    df = df.replace('div', 'text')
    # replace 'span' with 'text'
    df = df.replace('span', 'text')

    return df
