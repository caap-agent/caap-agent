from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = convert_df_base_formatting(df)

    # replace 'th' with 'text'
    df = df.replace('th', 'text')

    # replace 'div' with 'text'
    df = df.replace('div', 'text')

    # Submit --> button
    # find the row where 'text' is 'Submit' and change its 'type' to 'button'
    df.loc[df['text'] == 'Submit', 'type'] = 'button'

    return df
