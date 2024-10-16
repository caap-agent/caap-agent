from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = df[df['left'] >= 0]

    df = convert_df_base_formatting(df)

    # replace 'div' to 'tabled_text'
    df = df.replace('div', 'tabled_text')

    return df
