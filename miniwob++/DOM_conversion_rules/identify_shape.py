from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = convert_df_base_formatting(df)

    for idx, row in df.iterrows():
        if row['type'] in ['circle', 'triangle', 'rectangle']:
            df.loc[idx, 'subtype'] = df.loc[idx, 'type']
            df.loc[idx, 'type'] = 'shape'
        elif row['type'] in ['rect']:
            df.loc[idx, 'subtype'] = 'rectangle'
            df.loc[idx, 'type'] = 'shape'
        elif row['type'] in ['polygon']:
            df.loc[idx, 'subtype'] = 'triangle'
            df.loc[idx, 'type'] = 'shape'

    return df
