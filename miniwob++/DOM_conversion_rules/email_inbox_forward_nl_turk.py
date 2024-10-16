from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = convert_df_base_formatting(df)

    df = df.replace('h2', 'text')
    df = df.replace('div', 'text')
    df = df.replace('t', 'text')
    df = df.replace('span', 'icon')

    consec_icons = 0
    for idx, row in df.iterrows():
        if row['type'] == 'icon':
            consec_icons += 1
        else:
            consec_icons = 0

        if consec_icons == 1:
            df.loc[idx, 'subtype'] = 'search'
        elif consec_icons > 1:
            df.loc[idx - 1, 'subtype'] = 'delete'
            df.loc[idx, 'subtype'] = 'important'
        else:
            df.loc[idx, 'subtype'] = ""

    if df.loc[0, 'type'] == 'icon':
        df.loc[0, 'subtype'] = 'back'

    if df.loc[2, 'text'] == 'to:':
        df.loc[1, 'type'] = 'icon'
        df.loc[1, 'subtype'] = 'send'

    for _text in ['Reply', 'Forward']:
        tgt_condition = (df['type'] == 'text') * (df['text'] == _text)
        if len(df.loc[tgt_condition]) == 1:
            tgt_row_idx = df.loc[tgt_condition].index.tolist()[0] - 1
            tgt_row = df.loc[tgt_row_idx]
            if tgt_row['type'] == 'text' and tgt_row['text'] == '' and tgt_row['value'] == '':
                df.loc[tgt_row.name, 'type'] = 'icon'
                df.loc[tgt_row.name, 'subtype'] = _text.lower()

    return df
