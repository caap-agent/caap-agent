from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = convert_df_base_formatting(df)

    # replace 'td' with 'tabled_text'
    df = df.replace('td', 'tabled_text')

    return df
