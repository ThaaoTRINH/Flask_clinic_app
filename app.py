from flask import Flask, render_template, request, redirect
import pymysql
from datetime import date, datetime

app = Flask(__name__)

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Thao@1978'
app.config['MYSQL_DB'] = 'mysql'

# Create a pymysql connection object
mysql = pymysql.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    db=app.config['MYSQL_DB']
)

class Patient:
    def __init__(self, number_id, day, name, birth_year, address, phone, reason, details, note):
        self.number_id = number_id
        self.day = day
        self.name = name
        self.birth_year = birth_year
        self.address = address
        self.phone = phone or []
        self.reason = reason or []
        self.details = details or []
        self.note = note or []


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/goback')
def go_back():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():

    current_date_show = date.today().strftime('%d/%m/%Y')
    if request.method == 'POST':
        cur = mysql.cursor()
        cur.execute("SELECT MAX(number_ID) FROM clinic_patients")
        number_row = cur.fetchone()
        number_id = int(number_row[0]) + 1 if number_row[0] else 1
        cur.close()

        day = date.today().strftime('%Y-%m-%d')
        name = request.form['name']
        birth_year = request.form['birth_year']
        address = request.form['address']
        phone = request.form['phone']

        # Process the form submission
        reason = request.form.getlist('option')
        details = request.form.getlist('select_option')
        note = request.form['note'] if request.form['note'] != '' else None
        formatted_details_list = []
        details_list = []

        for n in range(len(details)):
            if details[n] != ' ':
                details_list.append(details[n])

        amount = 0
        formatted_amount = 0

        for i in range(len(reason)):
            cursor = mysql.cursor()
            cursor.execute(f"SELECT ID FROM reason WHERE name='{reason[i]}'")
            data1 = cursor.fetchall()
            cursor.close()
            reason_id = data1[0][0]

            cursor = mysql.cursor()
            cursor.execute(f"SELECT price FROM {reason_id} WHERE name='{details_list[i]}'")
            data2 = cursor.fetchall()
            cursor.close()
            price = data2[0][0]
            formatted_price = "{:,.0f}".format(price)
            amount += price
            formatted_amount = "{:,.0f}".format(amount)
            formatted_details_list.append(f"{reason[i]} ({details_list[i]}) | Thanh tien: {formatted_price}")

        # Convert reason and detail lists to strings
        reason_str = ','.join(reason)
        detail_str = ' , '.join(details)

        # Create a new patient instance
        patient = Patient(number_id, day, name, birth_year, address, phone, reason_str, detail_str, note)

        # Save the patient details to the database
        cur = mysql.cursor()
        cur.execute("INSERT INTO clinic_patients (number_ID, registration_date, name, birth_year, address, "
                    "phone, reason, details, note) VALUES "
                    "(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (patient.number_id, patient.day, patient.name, patient.birth_year, patient.address,
                     patient.phone, patient.reason, patient.details, formatted_amount))
        mysql.commit()
        cur.close()

        return render_template('patient_show.html', current_date=current_date_show, name=name.upper(),
                               birth_year=birth_year, address=address, phone=phone, reason=reason,
                               formatted_details_list=formatted_details_list, note=note, sum=formatted_amount)

    def fetch_data(table_name):
        cursor_data = mysql.cursor()
        cursor_data.execute(f"SELECT * FROM {table_name}")
        data = cursor_data.fetchall()
        cursor_data.close()
        return data

    sieu_am_details = fetch_data("sieu_am")
    xnht_details = fetch_data("xnht")
    xnm_details = fetch_data("xnm")
    pap_hpv_details = fetch_data("pap_hpv")
    vong_details = fetch_data("vong")
    que_details = fetch_data("que")
    msmp_details = fetch_data("msmp")
    khac_details = fetch_data("khac")
    current_date_show = date.today().strftime('%d/%m/%Y')
    return render_template('registration.html', current_date=current_date_show, sieu_am_details=sieu_am_details,
                           xnht_details=xnht_details, xnm_details=xnm_details, pap_hpv_details=pap_hpv_details,
                           vong_details=vong_details, que_details=que_details, msmp_details=msmp_details,
                           khac_details=khac_details)


@app.route('/patients', methods=['GET', 'POST'])
def patients():
    if request.method == 'GET':
        cur = mysql.cursor()
        cur.execute("SELECT * FROM clinic_patients")
        patients_data = cur.fetchall()
        cur.close()

        patients_list = []
        for data in patients_data:
            patient = Patient(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8])
            patients_list.append(patient)

        return render_template('patients_export.html', patients=patients_list, search='Theo thang')

@app.route('/patient_search', methods=['GET', 'POST'])
def patient_search():
    if request.method == 'POST':
        search_query = request.form['search_query']

        # Perform the search query in mysql
        cur = mysql.cursor()
        sql = """
               SELECT * FROM clinic_patients
               WHERE name LIKE %s
               OR (address LIKE %s AND %s != '')
               OR (phone LIKE %s AND %s != '')
               OR (birth_year = %s AND %s != '')
               """
        params = (
            '%' + search_query + '%',
            '%' + search_query + '%',
            '%' + search_query + '%',
            '%' + search_query + '%',
            search_query, search_query, search_query
        )

        cur.execute(sql, params)
        patients_data = cur.fetchall()
        cur.close()

        patients_list = []
        for data in patients_data:
            patient = Patient(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8])
            patients_list.append(patient)
        return render_template('patients_export.html', patients=patients_list, search='Theo thong tin bn')

    return render_template('registration.html')

@app.route('/filter/<keyword>', methods=['GET', 'POST'])
def filter_data(keyword):
    if request.method == 'POST':
        filter_from_month = request.form['filter_from_month']
        filter_from_year = request.form['filter_from_year']
        month = int(filter_from_month)
        year = int(filter_from_year)
    if request.method == 'GET':
        cur = mysql.cursor()
        cur.execute(f"SELECT name FROM reason WHERE ID='{keyword}'")
        key = cur.fetchall()
        cur.close()
        key_str = ','.join(key[0])

        cur = mysql.cursor()
        cur.execute(f"SELECT * FROM clinic_patients WHERE reason LIKE '%{key_str}%'")
        patients_data = cur.fetchall()
        cur.close()

        patients_list = []
        for data in patients_data:
            patient = Patient(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8])
            patients_list.append(patient)

        return render_template('patients_export.html', patients=patients_list, search=month)

@app.route('/patient_search_day', methods=['GET', 'POST'])
def patient_search_day():
    if request.method == 'POST':
        search_date = request.form['search_date']

        # Assuming you have a variable named 'search_date' containing the string date value
        datetime_obj = datetime.strptime(search_date, '%Y-%m-%d')
        formatted_search_date = datetime_obj.strftime('%Y-%m-%d')
        # return render_template('patient_search_date.html', search_date=formatted_search_date)

        # Perform the search query in mysql
        cur = mysql.cursor()
        sql = """
               SELECT * FROM clinic_patients
               WHERE registration_date = %s
               OR (registration_date = %s AND %s != '')
               """
        params = (
            formatted_search_date,
            formatted_search_date,
            formatted_search_date
        )

        cur.execute(sql, params)
        patients_data = cur.fetchall()
        cur.close()

        patients_list = []
        for data in patients_data:
            patient = Patient(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8])
            patients_list.append(patient)
        return render_template('patients_export.html', patients=patients_list, search=formatted_search_date)

    return render_template('registration.html')

@app.route('/search_dmy', methods=['GET', 'POST'])
def search_patient_daytoday():
    if request.method == 'POST':
        search_date = request.form['from_date']

        # Assuming you have a variable named 'search_date' containing the string date value
        datetime_obj = datetime.strptime(search_date, '%Y-%m-%d')
        formatted_search_date = datetime_obj.strftime('%Y-%m-%d')

        # # Perform the search query in mysql
        # cur = mysql.cursor()
        # sql = """
        #        SELECT * FROM clinic_patients
        #        WHERE registration_date = %s
        #        OR (registration_date = %s AND %s != '')
        #        """
        # params = (
        #     formatted_search_date,
        #     formatted_search_date,
        #     formatted_search_date
        # )
        #
        # cur.execute(sql, params)
        # patients_data = cur.fetchall()
        # cur.close()
        #
        # patients_list = []
        # for data in patients_data:
        #     patient = Patient(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8])
        #     patients_list.append(patient)
        return render_template('patients_export.html', search=formatted_search_date)

    return render_template('registration.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=True)