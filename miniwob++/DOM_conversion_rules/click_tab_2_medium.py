from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = convert_df_base_formatting(df)

    # replace 't' with 'text_field', etc
    df = df.replace('t', 'text')
    df = df.replace('span', 'hyperlink')
    df = df.replace('a', 'button')

    return df
