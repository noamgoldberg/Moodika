import streamlit as st
import pymysql

def show_explore_page():
    # st.title("More about us")

    st.image("moodika3.png")
    st.text("Noam, Doron and Sam are part of the 2022 Cohort from ITC - Israel Tech Challenge")
    st.write("We want to thank our mentor, Morris Alper, for his invaluable assistance in creating this and all the ITC Staff for their amazing support!")
    st.write("LinkedIn: [Doron](https://www.linkedin.com/in/doronreiffman/), [Noam](https://www.linkedin.com/in/noam-goldberg/), [Sam](https://www.linkedin.com/in/samuelnataf/)")
    st.write("Doron: Favorite artist - the Beatles; favorite genre - Forro")
    st.write("Noam: Favorite artist - John mayer; Favorite genre - Hip hop and rnb")
    st.write("Sam: Favorite artist - Jean-Jacques Goldman; Favorite genre - Acoustic")

    user = st.text_input("Your Name")
    art = st.text_input("Favorite Artist")
    genr = st.text_input("Favorite Genre")
    feed = st.text_input("Any feedback is appreciated ;)")

    ok2 = st.button("Submit")

    if ok2:

        connection = pymysql.connect(host=HOST,
                                     user=USER,
                                     password=PASSWORD,
                                     db=DB,
                                     port=PORT,
                                     cursorclass=pymysql.cursors.DictCursor
                                     )

        sql = "INSERT INTO moodika.Feedback (name, fav_artist, fav_genre, Feedback) VALUES (%s, %s, %s,%s)"
        val = (user, art, genr, feed)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, val)
                connection.commit()

        st.write("""Thanks for your feedback!""")
        st.balloons()