from DOM_conversion_rules import convert_df_base_formatting


def convert_df(df):
    df = convert_df_base_formatting(df)

    # replace 't' with 'text'
    df = df.replace('t', 'text')

    df.drop(['focused'], axis=1, inplace=True)

    valid_idx_list = list()
    for idx_chk, idx_txt in zip(df.index.tolist()[:-1], df.index.tolist()[1:]):
        if df.loc[idx_chk, 'type']=='checkbox' and df.loc[idx_txt, 'type']=='text':
            df.loc[idx_chk, 'text'] = df.loc[idx_txt, 'text']
            df.loc[idx_chk, 'x1'] = df.loc[idx_chk, 'x1'] + 3
            df.loc[idx_chk, 'x2'] = df.loc[idx_txt, 'x2']
            df.loc[idx_chk, 'y2'] = df.loc[idx_txt, 'y2']
            valid_idx_list.append(idx_chk)
        if df.loc[idx_txt, 'type']=='button':
            valid_idx_list.append(idx_txt)

    df = df.loc[valid_idx_list].reset_index(drop=True)

    return df
