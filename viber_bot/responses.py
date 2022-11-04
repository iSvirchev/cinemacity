import paths
from queries import *

db = DatabaseCommunication(paths.DB_PATH)


class Responses:
    info = 'Please type one of the following commands:\n\n' \
           '*Today* - will display today\'s movies on screen\n' \
           '*Tomorrow* - will display tomorrow\'s movies on screen\n' \
           '*Dates* - to check movies on screen for the selected date\n' \
           '*Cinemas* - to pick your favourite cinema\n' \
           '*Sub/Unsub* - to subscribed/unsubscribe for new movies in cinema updates'

    def movies(self, cinema_id, date,  movies_in_cinema):
        movies = list(movies_in_cinema.keys())
        cinema_name = db.fetch_cinema_by_id(cinema_id)[CinemasTable.CINEMA_NAME]

        movies_resp = 'Movies currently in *%s* for date *%s*:\n' % (cinema_name, date)
        for movie in movies:
            movies_resp + '\n' + movie

        return movies_resp

    def dates_kb(self, dates):
        keyboard = {
            "Type": "keyboard",
            "Buttons": []
        }

        colour_codes = ['#75ace1', '#df7779', '#d1b185', '#8187d5', '#00703c', '#7ac2dc', '#bc8dc9', '#727C96',
                        '#D9CBC1',
                        '#75ace1', '#df7779', '#d1b185', '#8187d5', '#00703c', '#7ac2dc', '#bc8dc9', '#727C96',
                        '#D9CBC1',
                        '#75ace1', '#df7779', '#d1b185', '#8187d5', '#00703c', '#7ac2dc', '#bc8dc9', '#727C96',
                        '#D9CBC1']

        button_tpl = {
            "Columns": 2,
            "Rows": 2,
            "BgColor": "#e6f5ff",  # <enter_colour_code_here>
            "BgLoop": True,
            "ActionType": "reply",
            "ActionBody": "<add_action_body>",
            "Text": "<add_btn_txt>",
        }
        for date in dates:
            day_btn = button_tpl.copy()  # we use .copy() as a simple assignment operator '=' gives us object reference
            day_btn['ActionBody'] = date
            day_btn['Text'] = '<font size=\"24\">%s</font>' % date
            day_btn['BgColor'] = colour_codes[dates.index(date)]
            keyboard['Buttons'].append(day_btn)

        return keyboard

    def movie_kb(self, movies_on_sel_date):
        keyboard = {
            "Type": "keyboard",
            "Buttons": []
        }

        m_btn_tpl = {
            "Columns": 2,
            "Rows": 2,
            "BgColor": "#e6f5ff",
            "BgLoop": True,
            "BgMedia": "<add_poster_link>",
            "ActionType": "",
            "ActionBody": "<add_action_body>",
            "TextOpacity": 0,
            "Text": "<add_btn_txt>"
        }

        for movie_id, movie in movies_on_sel_date.items():
            m_poster = movie['poster_link']
            m_name = movie['movie_name']

            day_btn = m_btn_tpl.copy()  # we use .copy() as a simple assignment operator '=' gives us object reference
            day_btn['ActionBody'] = m_name
            day_btn['Text'] = m_name
            day_btn['BgMedia'] = m_poster
            keyboard['Buttons'].append(day_btn)

        return keyboard

    def dates(self):
        dates_resp = 'Which day are you interested in?\n'
        # for day_resp in self.days_dictionary:
        #     dates_resp = dates_resp + '\n' + day_resp
        return dates_resp

    def cinemas_kb(self, cinemas):
        keyboard = {
            "Type": "keyboard",
            "Buttons": []
        }

        c_btn_tpl = {
            "Columns": 2,
            "Rows": 2,
            "BgColor": "#e6f5ff",
            "BgLoop": True,
            "BgMedia": "<add_poster_link>",
            "ActionType": "",
            "ActionBody": "<add_action_body>",
            "Text": "<add_btn_txt>",
            "TextSize": "regular",
            "TextVAlign": "middle",
        }
        for cinema_id, cinema in cinemas.items():
            cinema_name = cinema['cinema_name']
            day_btn = c_btn_tpl.copy()  # we use .copy() as a simple assignment operator '=' gives us object reference
            day_btn['ActionBody'] = cinema_name
            day_btn['Text'] = "<font color=\"#ffffff\"><b>%s</b></font>" % cinema_name
            day_btn['BgMedia'] = cinema['image_url']
            keyboard['Buttons'].append(day_btn)

        return keyboard
