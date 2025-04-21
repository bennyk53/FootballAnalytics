import streamlit as st
import pymongo
import pandas as pd
import numpy as np
import xlsxwriter
import warnings
warnings.filterwarnings('ignore')

def writer(r, c, maxR, dataset, subset, worksheet, subheader, part):

  totalPlays = len(dataset)
  if (totalPlays > 0):
    startingC = c

    if (part):
      subTimes = sum(subset.values())

    if (part):
      worksheet.write(r,c,subheader + ' - '+str(subTimes)+" ("+str(round((subTimes/totalPlays)*100,3)) + '%)')
    else:
      worksheet.write(r,c, subheader + ' - '  +str(totalPlays))

  r += 1
  for key, value in subset.items():
    worksheet.write(r,c,key)
    c += 1
    worksheet.write(r,c,value)
    c += 1
    if (part):
      worksheet.write(r,c,str(round((value/subTimes)*100,3))+'%')
    else:
      worksheet.write(r,c,str(round((value/totalPlays)*100,3))+'%')
    c = startingC
    r += 1

  if (r > maxR):
      maxR = r

  c += 4

  return r,c, maxR, worksheet

def writeByForm(r,c,maxR,worksheet, formList, col, df):

  startingR = r

  for f in formList:
    startingC = c
    worksheet.write(r,c,f)
    temp = df.loc[df['FORMATION'] == f].groupby(col).size().sort_values(ascending=False).to_dict()
    r += 1
    for key, value in temp.items():
      worksheet.write(r,c,key)
      c += 1
      worksheet.write(r,c,value)
      c += 1
      worksheet.write(r,c,str(round((value/sum(temp.values()))*100,3))+'%')
      c = startingC
      r += 1

    if (r > maxR):
      maxR = r

    c += 4
    r = startingR

  return r,c, maxR, worksheet



def writeAByB(r,c, maxR, set, aByB, worksheet):

  startingR = r

  for abb in aByB:
    startingC = c

    varTimes = sum(abb[1].values())
    reps = set[abb[0]]

    worksheet.write(r,c,abb[0]+ ' (' +str(reps) + ') '+ str(round((varTimes/reps) *100,3)) + '%')
    r += 1
    for key, value in abb[1].items():
      worksheet.write(r,c,key)
      c += 1
      worksheet.write(r,c,value)
      c += 1
      worksheet.write(r,c,str(round((value/varTimes)*100,3))+'%')
      r += 1
      c = startingC

    if (r > maxR):
      maxR = r

    c += 4
    r = startingR

  c += 4

  return r,c, maxR, worksheet





def reset(maxR):
  r = maxR + 2
  c = 0
  lastR = maxR + 2

  return r,c,lastR

# Session state to track login
if 'login' not in st.session_state:
    st.session_state['login'] = False

if 'generated' not in st.session_state:
    st.session_state['generated'] = False

if 'uploaded' not in st.session_state:
    st.session_state['uploaded'] = True

def login():
    st.title("🔐 Login Page")

    client = pymongo.MongoClient("mongodb+srv://ben:ben@footballanalytics.h4h8bcs.mongodb.net/?retryWrites=true&w=majority&appName=FootballAnalytics")
    mydb = client["FootballAnalytics"]
    mycol = mydb["users"]

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            results = mycol.find({'username' : username, 'password' : password})
            if len(list(results)) == 1:
                st.session_state['login'] = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")

def toggleUploaded():
  st.session_state['uploaded'] = not(st.session_state['uploaded'])

def main_app():
    if st.button("Logout"):
        st.session_state['login'] = False
        st.rerun()
        
    uploaded_file = st.file_uploader("Choose a file",on_change=toggleUploaded(),disabled=st.session_state['uploaded'])

    if uploaded_file is None:
      st.session_state['generated'] = False
    

    if st.session_state['generated'] and uploaded_file is not None:
        with open("test.xlsx", "rb") as file:
            btn = st.download_button(
                label="Download Breakdown",
                data=file,
                file_name=uploaded_file.name.split('.')[0]+" breakdown.xlsx",
                #mime="text/csv"
              )              
    
    if uploaded_file is not None and not(st.session_state['generated']):
        df = pd.read_csv(uploaded_file)

        #df = pd.read_csv('/content/drive/MyDrive/SportsAnalytics/Football/Waterloo SCOUT REPORTS/QUE/scoutCSVs/QUEENS D COMPLETE.csv')
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        df.drop(df[df['FORMATION'] == 'KNEEL'].index, inplace = True)
        #df = df.replace('3DH','DBL HOLD')
        #df = df.replace('3DC','DBL CUT')
        #df = df.replace('41H','41 HOLD')
        #df = df.replace('41C','41 CUT')
        #df = df.replace('31H','31 HOLD')
        #df = df.replace('31C','31 CUT')

        #df = df.replace('^4 ....$','Cover 4', regex = True)


        workbook = xlsxwriter.Workbook('test.xlsx')

        # workbook formats
        bold = workbook.add_format({'bold':True})

        #overall
        blitzes = df.groupby('BLITZ TYPE').size().sort_values(ascending=False).to_dict()
        stunts = df.groupby('STUNT TYPE').size().sort_values(ascending=False).to_dict()
        fronts = df.groupby('FRONT').size().sort_values(ascending=False).to_dict()
        coverages = df.groupby('COVER').size().sort_values(ascending=False).to_dict()
        forms = df.groupby('FORMATION').size().sort_values(ascending=False).to_dict()

        #D&D
        firstAndTen = df.loc[(df['DN'] == 1) & (df['DST'] == 10)]
        secondAndShort = df.loc[(df['DN'] == 2) & (df['DST'] <= 3)]
        secondAndMed = df.loc[(df['DN'] == 2) & (df['DST'] <= 7) & (df['DST'] >= 4)]
        secondAndLong = df.loc[(df['DN'] == 2) & (df['DST'] >= 8)]

        #field zones
        redzone = df.loc[(df['FIELD POS'] > 0) & (df['FIELD POS'] <= 20)]
        scorezone = df.loc[(df['FIELD POS'] > 20) & (df['FIELD POS'] <= 45)]
        freezone = df.loc[(df['FIELD POS'] > 45) | (df['FIELD POS'] < -35)]
        winzone = df.loc[(df['FIELD POS'] >= -35) & (df['FIELD POS'] < 0)]

        #1st 10
        blitzes1 = firstAndTen.groupby('BLITZ TYPE').size().sort_values(ascending=False).to_dict()
        fronts1 = firstAndTen.groupby('FRONT').size().sort_values(ascending=False).to_dict()
        coverages1 = firstAndTen.groupby('COVER').size().sort_values(ascending=False).to_dict()
        stunts1 = firstAndTen.groupby('STUNT TYPE').size().sort_values(ascending=False).to_dict()
        frontAdj1 = firstAndTen.groupby('FRONT ADJUST').size().sort_values(ascending=False).to_dict()

        #2nd short
        blitzes2s = secondAndShort.groupby('BLITZ TYPE').size().sort_values(ascending=False).to_dict()
        fronts2s = secondAndShort.groupby('FRONT').size().sort_values(ascending=False).to_dict()
        coverages2s = secondAndShort.groupby('COVER').size().sort_values(ascending=False).to_dict()
        stunts2s = secondAndShort.groupby('STUNT TYPE').size().sort_values(ascending=False).to_dict()
        frontAdj2s = secondAndShort.groupby('FRONT ADJUST').size().sort_values(ascending=False).to_dict()

        #2nd med
        blitzes2m = secondAndMed.groupby('BLITZ TYPE').size().sort_values(ascending=False).to_dict()
        fronts2m = secondAndMed.groupby('FRONT').size().sort_values(ascending=False).to_dict()
        coverages2m = secondAndMed.groupby('COVER').size().sort_values(ascending=False).to_dict()
        stunts2m = secondAndMed.groupby('STUNT TYPE').size().sort_values(ascending=False).to_dict()
        frontAdj2m = secondAndMed.groupby('FRONT ADJUST').size().sort_values(ascending=False).to_dict()


        #2nd long
        blitzes2l = secondAndLong.groupby('BLITZ TYPE').size().sort_values(ascending=False).to_dict()
        fronts2l = secondAndLong.groupby('FRONT').size().sort_values(ascending=False).to_dict()
        coverages2l = secondAndLong.groupby('COVER').size().sort_values(ascending=False).to_dict()
        stunts2l = secondAndLong.groupby('STUNT TYPE').size().sort_values(ascending=False).to_dict()
        frontAdj2l = secondAndLong.groupby('FRONT ADJUST').size().sort_values(ascending=False).to_dict()

        #redzone
        blitzesrz = redzone.groupby('BLITZ TYPE').size().sort_values(ascending=False).to_dict()
        frontsrz = redzone.groupby('FRONT').size().sort_values(ascending=False).to_dict()
        coveragesrz = redzone.groupby('COVER').size().sort_values(ascending=False).to_dict()
        stuntsrz = redzone.groupby('STUNT TYPE').size().sort_values(ascending=False).to_dict()

        #scorezone
        blitzessz = scorezone.groupby('BLITZ TYPE').size().sort_values(ascending=False).to_dict()
        frontssz = scorezone.groupby('FRONT').size().sort_values(ascending=False).to_dict()
        coveragessz = scorezone.groupby('COVER').size().sort_values(ascending=False).to_dict()
        stuntssz = scorezone.groupby('STUNT TYPE').size().sort_values(ascending=False).to_dict()

        #freezone
        blitzesfz = freezone.groupby('BLITZ TYPE').size().sort_values(ascending=False).to_dict()
        frontsfz = freezone.groupby('FRONT').size().sort_values(ascending=False).to_dict()
        coveragesfz = freezone.groupby('COVER').size().sort_values(ascending=False).to_dict()
        stuntsfz = freezone.groupby('STUNT TYPE').size().sort_values(ascending=False).to_dict()

        #winzone
        blitzeswz = winzone.groupby('BLITZ TYPE').size().sort_values(ascending=False).to_dict()
        frontswz = winzone.groupby('FRONT').size().sort_values(ascending=False).to_dict()
        coverageswz = winzone.groupby('COVER').size().sort_values(ascending=False).to_dict()
        stuntswz = winzone.groupby('STUNT TYPE').size().sort_values(ascending=False).to_dict()

        #blitzes by front
        frontList = df.groupby('FRONT').size().index.tolist()
        blitz = df.loc[df['BLITZ'] == 'Y']
        blitzesByFront = []
        for f in frontList:
            frontBlitzes = blitz.loc[blitz['FRONT'] == f].groupby('BLITZ TYPE').size().sort_values(ascending=False).to_dict()
            blitzesByFront.append([f,frontBlitzes])

        # variation by coverage
        coverageList = df.groupby('COVER').size().index.tolist()
        varByCov = []
        for c in coverageList:
            covVar = df.loc[df['COVER'] == c].groupby('VARIATION').size().sort_values(ascending=False).to_dict()
            varByCov.append([c,covVar])

        # adjust by front
        adjByFront = []
        for f in frontList:
            frontAdj = df.loc[df['FRONT'] == f].groupby('FRONT ADJUST').size().sort_values(ascending=False).to_dict()
            adjByFront.append([f,frontAdj])

        # adjust by formation
        adjFormList = df.groupby('FORMATION').size().index.tolist()
        adjByForm = []
        for f in adjFormList:
            frontAdj = df.loc[df['FORMATION'] == f].groupby('FRONT ADJUST').size().sort_values(ascending=False).to_dict()
            adjByForm.append([f,frontAdj])

        # blitz by formation
        blitzFormList = df.loc[df['BLITZ'] == 'Y'].groupby('FORMATION').size().index.tolist()
        blitzByForm = []
        for c in blitzFormList:
            blitzForm = df.loc[df['FORMATION'] == c].groupby('BLITZ TYPE').size().sort_values(ascending=False).to_dict()
            blitzByForm.append([c,blitzForm])


        formations = df['FORMATION'].to_list()
        formList = list(dict.fromkeys(formations))

        # Coverages =================================================================================

        worksheet = workbook.add_worksheet("Coverages")

        r = 0
        c = 0

        maxR = 0

        worksheet.write(r,c,'Coverage by Formation', bold)
        r += 1

        r,c, maxR, worksheet = writeByForm(r,c,maxR,worksheet,formList,'COVER',df)

        worksheet.write(maxR+1,0,'Coverage by D&D',bold)

        #1 and 10
        r,c,lastR = reset(maxR)

        r,c, maxR, worksheet = writer (r,c,maxR,firstAndTen,coverages1, worksheet,'1st and 10', False)
        r = lastR

        #2 and 1-3 (short)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndShort,coverages2s, worksheet,'2nd and 1-3', False)
        r = lastR

        #2 and 4-7 (med)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndMed,coverages2m, worksheet,'2nd and 4-7', False)
        r = lastR


        #2 and 7+ (long)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndLong,coverages2l, worksheet,'2nd and 7+', False)
        r = lastR


        worksheet.write(maxR+1,0,'Coverage by Field Zone',bold)
        r,c,lastR = reset(maxR)

        # red zone
        r,c,maxR,worksheet = writer (r,c,maxR,redzone,coveragesrz,worksheet,'Red Zone (0-20)', False)
        r = lastR

        # score zone
        r,c,maxR,worksheet = writer (r,c,maxR,scorezone,coveragessz,worksheet,'Score Zone (20-45)', False)
        r = lastR

        # free zone
        r,c,maxR,worksheet = writer (r,c,maxR,freezone,coveragesfz,worksheet,'Free Zone (45-35)', False)
        r = lastR

        # win zone
        r,c,maxR,worksheet = writer (r,c,maxR,winzone,coverageswz,worksheet,'Win Zone (35-0)', False)
        r = lastR

        worksheet.write(maxR+1,0,'Variation by Coverage',bold)
        r,c,lastR = reset(maxR)
        r,c,maxR,worksheet = writeAByB(r,c, maxR, coverages,varByCov,worksheet)

        # Blitzes =============================================================================

        worksheet = workbook.add_worksheet("Blitzes")

        r,c,lastR,maxR = 0,0,0,0

        worksheet.write(r,c,'Blitz by D&D',bold)
        r += 1
        lastR += 1

        #1st and 10
        r,c,maxR,worksheet = writer (r,c,maxR,firstAndTen,blitzes1,worksheet,'1st and 10', True)
        r = lastR

        #2 and 1-3 (short)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndShort,blitzes2s, worksheet,'2nd and 1-3', True)
        r = lastR

        #2 and 4-7 (med)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndMed,blitzes2m, worksheet,'2nd and 4-7', True)
        r = lastR


        #2 and 7+ (long)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndLong,blitzes2l, worksheet,'2nd and 7+', True)
        r = lastR

        worksheet.write(maxR+1,0,'Blitz by Field Zone',bold)
        r,c,lastR = reset(maxR)

        # red zone
        r,c,maxR,worksheet = writer (r,c,maxR,redzone,blitzesrz,worksheet,'Red Zone (0-20)', True)
        r = lastR

        # score zone
        r,c,maxR,worksheet = writer (r,c,maxR,scorezone,blitzessz,worksheet,'Score Zone (20-45)', True)
        r = lastR

        # free zone
        r,c,maxR,worksheet = writer (r,c,maxR,freezone,blitzesfz,worksheet,'Free Zone (45-35)', True)
        r = lastR

        # win zone
        r,c,maxR,worksheet = writer (r,c,maxR,winzone,blitzeswz,worksheet,'Win Zone (35-0)', True)
        r = lastR

        # blitz by front
        worksheet.write(maxR+1,0,'Blitz by Front',bold)
        r,c,lastR = reset(maxR)
        r,c,maxR,worksheet = writeAByB(r,c, maxR,fronts,blitzesByFront,worksheet)

        # blitz by formation
        worksheet.write(maxR+1,0,'Blitz by Formation',bold)
        r,c,lastR = reset(maxR)
        r,c,maxR,worksheet = writeAByB(r,c, maxR, forms,blitzByForm,worksheet)

        # Fronts ===================================================================================
        worksheet = workbook.add_worksheet("Fronts")

        r,c,lastR,maxR = 0,0,0,0

        worksheet.write(r,c,'Fronts by D&D',bold)
        r += 1
        lastR += 1

        #1st and 10
        r,c,maxR,worksheet = writer (r,c,maxR,firstAndTen,fronts1,worksheet,'1st and 10', False)
        r = lastR

        #2 and 1-3 (short)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndShort,fronts2s, worksheet,'2nd and 1-3', False)
        r = lastR

        #2 and 4-7 (med)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndMed,fronts2m, worksheet,'2nd and 4-7', False)
        r = lastR


        #2 and 7+ (long)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndLong,fronts2l, worksheet,'2nd and 7+', False)
        r = lastR

        # front adjust by front
        worksheet.write(maxR+1,0,'Front Adjustment by Front',bold)
        r,c,lastR = reset(maxR)
        r,c,maxR,worksheet = writeAByB(r,c, maxR,fronts,adjByFront,worksheet)

        #front adjust by d&d
        worksheet.write(maxR+1,0,'Front Adjustment by D&D',bold)
        r,c,lastR = reset(maxR)

        #1st and 10
        r,c,maxR,worksheet = writer (r,c,maxR,firstAndTen,frontAdj1,worksheet,'1st and 10', False)
        r = lastR

        #2 and 1-3 (short)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndShort,frontAdj2s, worksheet,'2nd and 1-3', False)
        r = lastR

        #2 and 4-7 (med)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndMed,frontAdj2m, worksheet,'2nd and 4-7', False)
        r = lastR

        #2 and 7+ (long)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndLong,frontAdj2l, worksheet,'2nd and 7+', False)
        r = lastR

        # front adjust by form
        worksheet.write(maxR+1,0,'Front Adjustment by Formations',bold)
        r,c,lastR = reset(maxR)
        r,c,maxR,worksheet = writeAByB(r,c, maxR, forms,adjByForm,worksheet)



        # Stunts =========================================================================================
        worksheet = workbook.add_worksheet("Stunts")

        r,c,lastR,maxR = 0,0,0,0

        worksheet.write(r,c,'Stunt by D&D',bold)
        r += 1
        lastR += 1

        #1st and 10
        r,c,maxR,worksheet = writer (r,c,maxR,firstAndTen,stunts1,worksheet,'1st and 10', True)
        r = lastR

        #2 and 1-3 (short)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndShort,stunts2s, worksheet,'2nd and 1-3', True)
        r = lastR

        #2 and 4-7 (med)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndMed,stunts2m, worksheet,'2nd and 4-7', True)
        r = lastR


        #2 and 7+ (long)
        r,c, maxR, worksheet = writer (r,c,maxR,secondAndLong,stunts2l, worksheet,'2nd and 7+', True)
        r = lastR

        workbook.close()
        st.session_state['generated'] = True
        st.rerun()


# Control flow
if st.session_state['login']:
    main_app()
else:
    login()
