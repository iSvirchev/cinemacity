class Responses:
    def __init__(self, days_dictionary):
        self.days_dictionary = days_dictionary

    info = 'Please type one of the following commands:\n\n' \
           '*Today* - will display today\'s movies on screen\n' \
           '*Tomorrow* - will display tomorrow\'s movies on screen\n' \
           '*Dates* - will provide you with buttons of dates from which you can choose.'

    def movies(self, movies_resp_day):
        movies_resp = '*Movies currently in cinema for date %s*\n' % movies_resp_day
        for movie_resp in self.days_dictionary[movies_resp_day]:
            movies_resp = movies_resp + '\n' + movie_resp
        return movies_resp

    def days_keyboard(self, days_arr):
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
            "Text": "<add_btn_txt>"
        }
        for day in days_arr:
            day_btn = button_tpl.copy()  # we use .copy() as a simple assignment operator '=' gives us object reference
            day_btn['ActionBody'] = day
            day_btn['Text'] = '<font size=\"24\">%s</font>' % day
            day_btn['BgColor'] = colour_codes[days_arr.index(day)]
            keyboard['Buttons'].append(day_btn)

        return keyboard

    def movie_keyboard(self, movie_kb_day):
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
            "Text": "<add_btn_txt>"
        }

        for m_key, m_value in self.days_dictionary[movie_kb_day].items():
            # m_poster = m_value['poster_link']

            day_btn = m_btn_tpl.copy()  # we use .copy() as a simple assignment operator '=' gives us object reference
            day_btn['ActionBody'] = m_value['movie_name']
            # day_btn['Text'] = "<font size=\"12\">%s</font>" % m_name
            day_btn['Text'] = m_value['movie_name']
            # day_btn['BgMedia'] = m_poster
            keyboard['Buttons'].append(day_btn)

        return keyboard

    def movie(self, movie_resp_day, movie_resp_movie):
        m_resp = 'Screenings of movie *%s* on *%s*\n\n' % (movie_resp_movie, movie_resp_day)
        screenings = self.days_dictionary[movie_resp_day][movie_resp_movie]['movie_screenings']
        m_resp = m_resp + '\n'.join(screenings)
        return m_resp

    def dates(self):
        dates_resp = 'Which day are you interested in?\n'
        for day_resp in self.days_dictionary:
            dates_resp = dates_resp + '\n' + day_resp
        return dates_resp
