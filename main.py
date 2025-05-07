import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date as dt, timedelta as td
from calendar import monthrange

import holidays
from dateutil import tz

tzinfo = tz.gettz('America/Sao_Paulo')

st.session_state.conn = st.connection('gsheets', type=GSheetsConnection)

def troca_update():
    st.session_state.troca = st.session_state.conn.read(worksheet='TROCA', ttl=60)
    st.session_state.troca['DE'] = pd.to_datetime(st.session_state.troca.DE, dayfirst=True)
    st.session_state.troca['PARA'] = pd.to_datetime(st.session_state.troca.PARA, dayfirst=True)
    return st.session_state.troca

def licpag_update():
    st.session_state.licpag = st.session_state.conn.read(worksheet='LICPAG', ttl=60)
    st.session_state.licpag['DATA'] = pd.to_datetime(st.session_state.licpag['DATA'], dayfirst=True).dt.date
    return st.session_state.licpag

def efetivo_update():
    st.session_state.efetivo_predio = st.session_state.conn.read(worksheet='EMB_PREDIO', ttl=60)
    st.session_state.efetivo_predio['EMBARQUE'] = pd.to_datetime(st.session_state.efetivo_predio['EMBARQUE'], dayfirst=True).dt.date
    st.session_state.efetivo_predio['DESEMBARQUE'] = pd.to_datetime(st.session_state.efetivo_predio['DESEMBARQUE'], dayfirst=True).dt.date
    
    st.session_state.efetivo_avipa = st.session_state.conn.read(worksheet='EMB_AVIPA', ttl=60)
    st.session_state.efetivo_avipa['EMBARQUE'] = pd.to_datetime(st.session_state.efetivo_avipa['EMBARQUE'], dayfirst=True).dt.date
    st.session_state.efetivo_avipa['DESEMBARQUE'] = pd.to_datetime(st.session_state.efetivo_avipa['DESEMBARQUE'], dayfirst=True).dt.date
    
    return st.session_state.efetivo_predio, st.session_state.efetivo_avipa

def restrito_update():
    st.session_state.restrito = st.session_state.conn.read(worksheet='REST', ttl=60)
    st.session_state.restrito['INICIAL'] = pd.to_datetime(st.session_state.restrito['INICIAL'], dayfirst=True).dt.date
    st.session_state.restrito['FINAL'] = pd.to_datetime(st.session_state.restrito['FINAL'], dayfirst=True).dt.date
    st.session_state.restrito.loc[st.session_state.restrito.MOTIVO=='Férias', 'INICIAL'] = st.session_state.restrito.loc[st.session_state.restrito.MOTIVO=='Férias', 'INICIAL'] - td(days=1)
    st.session_state.restrito.loc[st.session_state.restrito.MOTIVO=='Viagem', 'FINAL'] = st.session_state.restrito.loc[st.session_state.restrito.MOTIVO=='Viagem', 'FINAL'] + td(days=1)
    return st.session_state.restrito

ano = 2025
meses = ['-', 'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

datas = [dt(ano, 1, 1) + td(i) for i in range(365)]

feriados = holidays.Brazil()['{}-01-01'.format(ano): '{}-12-31'.format(ano)] + [dt(ano, 6, 11), dt(ano, 12, 13)]

vermelha, preta = [], []

licpag = licpag_update()
for d in datas:
    #  final de semana           feriados           licpag
    if (d.weekday() in (5,6)) or (d in feriados) or (d in licpag.DATA.values):
        vermelha.append(d)
    else:
        preta.append(d)

for d in vermelha:
    if (d + td(2) in vermelha) and (d + td(1) not in vermelha):
        vermelha.append(d + td(1))
        preta.remove(d + td(1))

vermelha.sort()

def get_disponivel(data, efetivo, restrito):
    disp = list(efetivo.NOME.values)
    data = pd.to_datetime(data)
    for i in efetivo[(pd.to_datetime(efetivo.EMBARQUE) > data) | (pd.to_datetime(efetivo.DESEMBARQUE) <= data)].NOME.values:
        disp.remove(i)
    for i in restrito[(pd.to_datetime(restrito.INICIAL) <= data) & (pd.to_datetime(restrito.FINAL) >= data)].NOME.unique():
        if i in disp:
            disp.remove(i)
    return disp

def que_se_segue(passa, efetivo, hoje, tabela):
    efetivos = list(efetivo.NOME.values)
    # if tabela == 'p':
    efetivos = efetivos[::-1]
    for i in range(1, len(efetivos)):
        cara = efetivos[efetivos.index(passa) - i]
        if cara in hoje:
            return cara
    

esc_preta = pd.DataFrame({'DATA':preta})
esc_vermelha = pd.DataFrame({'DATA':vermelha})
esc_corrida = pd.DataFrame({'DATA':datas})


#######################Ajustar os primeiros ASD
esc_preta.loc[esc_preta.DATA == dt(2025, 1, 6), 'C1'] = '2SG-MC ROGÉRIO'
esc_vermelha.loc[esc_vermelha.DATA == dt(2025, 1, 1), 'C1'] = '3SG-MT GURGEL'
esc_corrida.loc[esc_corrida.DATA == dt(2025,1,1), 'C2'] = '2SG-MR FERDINAND'


esc_preta.set_index('DATA', inplace=True)
esc_vermelha.set_index('DATA', inplace=True)
esc_corrida.set_index('DATA', inplace=True)

restrito = restrito_update()
efetivo_predio, efetivo_avipa = efetivo_update()

for d in esc_preta.index[1:]:
    ontem_predio = get_disponivel(preta[preta.index(d) - 1], efetivo_predio, restrito)
    hoje_predio = get_disponivel(d, efetivo_predio, restrito)
    hoje_predio = hoje_predio + hoje_predio
    passa_predio = esc_preta.loc[preta[preta.index(d) - 1], 'C1']

    ontem_avipa = get_disponivel(datas[datas.index(d) - 1], efetivo_avipa, restrito)
    hoje_avipa = get_disponivel(d, efetivo_avipa, restrito)
    hoje_avipa = hoje_avipa + hoje_avipa
    passa_avipa = esc_corrida.loc[datas[datas.index(d) - 1], 'C2']

    try:
        esc_preta.loc[d, 'C1'] = que_se_segue(passa_predio, efetivo_predio, hoje_predio, 'p')
        esc_corrida.loc[d, 'C2'] = que_se_segue(passa_avipa, efetivo_avipa, hoje_avipa, 'c')
    except Exception as e:
        st.write(e)
        pass
    

for d in esc_vermelha.index[1:]:
    ontem_predio = get_disponivel(vermelha[vermelha.index(d) - 1], efetivo_predio, restrito)
    hoje_predio = get_disponivel(d, efetivo_predio, restrito)
    passa_predio = esc_vermelha.loc[vermelha[vermelha.index(d) - 1], 'C1']

    ontem_avipa = get_disponivel(datas[datas.index(d) - 1], efetivo_avipa, restrito)
    hoje_avipa = get_disponivel(d, efetivo_avipa, restrito)
    passa_avipa = esc_corrida.loc[datas[datas.index(d) - 1], 'C2']

    try:
        esc_vermelha.loc[d, 'C1'] = que_se_segue(passa_predio, efetivo_predio, hoje_predio, 'v')
        esc_corrida.loc[d, 'C2'] = que_se_segue(passa_avipa, efetivo_avipa, hoje_avipa, 'c')
    except Exception as e:
        st.write(e)
        pass

esc_preta.loc[:,'C2'] = esc_corrida.loc[esc_preta.index].C2
esc_vermelha.loc[:,'C2'] = esc_corrida.loc[esc_vermelha.index].C2
geral_corrida = pd.concat([esc_preta, esc_vermelha]).sort_index()

troca = troca_update()
geral_corrida.index = pd.to_datetime(geral_corrida.index)
for i, row in troca.iterrows():
    troc1 = geral_corrida.loc[row.DE, 'NOME']
    troc2 = geral_corrida.loc[row.PARA, 'NOME']
    geral_corrida.loc[row.DE, 'NOME'] = troc2
    geral_corrida.loc[row.PARA, 'NOME'] = troc1
    
gera_mes = dt.today().month # meses.index(st.selectbox('Gerar tabela do mês:', meses))

df1 = pd.DataFrame({'DIA': [d for d in datas if d.month == gera_mes], 'TABELA':['V' if d in vermelha else 'P' for d in datas if d.month == gera_mes], 'C1':[geral_corrida.loc[pd.to_datetime(d), 'C1'] for d in datas if d.month == gera_mes], 'C2':[geral_corrida.loc[pd.to_datetime(d), 'C2'] for d in datas if d.month == gera_mes]})
df2 = pd.DataFrame({'DIA': [d for d in datas if d.month == (gera_mes+1)%12], 'TABELA':['V' if d in vermelha else 'P' for d in datas if d.month == (gera_mes+1)%12], 'C1':[geral_corrida.loc[pd.to_datetime(d), 'C1'] for d in datas if d.month == (gera_mes+1)%12], 'C2':[geral_corrida.loc[pd.to_datetime(d), 'C2'] for d in datas if d.month == (gera_mes+1)%12]})

if dt.today() in preta:
    retem1 = preta[preta.index(dt.today())+2]
elif dt.today() in vermelha:
    retem1 = vermelha[vermelha.index(dt.today()) + 2]

if (dt.today() + td(days=1)) in preta:
    retem2 = preta[preta.index(dt.today() + td(days=1))+2]
elif (dt.today() + td(days=1)) in vermelha:
    retem2 = vermelha[vermelha.index(dt.today() + td(days=1)) + 2]

# col1, col2 = st.columns(2)

# with col1:
st.title(f'Contramestres de {dt.today().strftime('%d/%m')}:')
st.markdown(f'<h3>{geral_corrida.loc[pd.to_datetime(dt.today()), 'C1']}; e</h3>', unsafe_allow_html=True)
st.markdown(f'<h3>{geral_corrida.loc[pd.to_datetime(dt.today()), 'C2']}.</h3>', unsafe_allow_html=True)
st.markdown(f'<h6>Retém: {geral_corrida.loc[pd.to_datetime(retem1)].iloc[0]}</h6>', unsafe_allow_html=True)
st.divider()    
st.title(f'Tabela de {meses[gera_mes]}')
df1 = df1[df1.DIA>=dt.today()]
df1['DIA'] = pd.to_datetime(df1.DIA).dt.strftime('%d/%m/%Y')
df1 = df1.set_index('DIA')
st.dataframe(df1.T, hide_index=True)#, height=1125)
st.session_state.conn.update(worksheet=meses[gera_mes], data=df1)
    # st.write('Conflitos:')
    # st.write(pd.DataFrame(filtra(gera_mes, conflitos)).T.rename(columns={0:'DE', 1:'PARA'}))


# with col2:
#    st.title(f'Contramestres de {(dt.today() + td(days=1)).strftime('%d/%m')}:')
#    st.markdown(f'<h3>{geral_corrida.loc[pd.to_datetime(dt.today() + td(days=1)), 'C1']}; e</h3>', unsafe_allow_html=True)
#    st.markdown(f'<h3>{geral_corrida.loc[pd.to_datetime(dt.today() + td(days=1)), 'C2']}.</h3>', unsafe_allow_html=True)
#    st.markdown(f'<h6>Retém: {geral_corrida.loc[pd.to_datetime(retem2)].iloc[0]}</h6>', unsafe_allow_html=True)
#    st.divider()  
#    st.title(f'Tabela de {meses[(gera_mes+1)%12]}')
#    df2['DIA'] = pd.to_datetime(df2.DIA).dt.strftime('%d/%m/%Y')
#    st.dataframe(df2, hide_index=True, height=1125)
#    st.session_state.conn.update(worksheet=meses[(gera_mes+1)%12], data=df2)
    # st.write('Conflitos:')
    # st.write(pd.DataFrame(filtra(gera_mes+1, conflitos)).T.rename(columns={0:'DE', 1:'PARA'}))

