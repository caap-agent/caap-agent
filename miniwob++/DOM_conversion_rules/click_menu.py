from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = convert_df_base_formatting(df)

    # replace 'div','t' to 'tabled_text'
    df = df.replace('div', 'tabled_text')
    df = df.replace('t', 'tabled_text')
    # replace 'span' to 'text'
    df = df.replace('span', 'text')

    return df
