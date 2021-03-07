import pandas as pd
import time

def addAnnotations(results, tokens):


    df = pd.DataFrame(results, columns=['start','end','nlp_cuis'])
    df['annotated'] = True


    df_tokens = pd.DataFrame(tokens['tokens'])
    df_tokens['annotated'] = False
    df_tokens['nlp_cuis'] = ''
    df_tokens = df_tokens.drop(columns=['id'])
        
    big_df = df_tokens.append(df, ignore_index=True)
    big_df= big_df.sort_values(['start','end'])

    big_df = big_df.drop_duplicates('start', keep='last')
    big_df = big_df.drop_duplicates('end', keep='first')

    return big_df.to_dict('records')
  
