import base64

from flask import Flask, request, render_template, jsonify
import pickle
import numpy as np
import plotly.express as px
import pandas as pd
from matplotlib import pyplot as plt
from plotly.subplots import make_subplots
import seaborn as sns

app = Flask(__name__)

# Load the RandomForestRegressor model
with open('model_random_forest.pkl', 'rb') as file:
    model = pickle.load(file)

# Load car data (replace 'cleaned_cars_data.csv' with your actual CSV file)
cars_data = pd.read_csv('cleaned_cars_data.csv')
selected_features = ['year', 'hp', 'cylinders', 'doors', 'highway_mpg', 'city_mpg', 'popularity', 'price']
subset_data = cars_data[selected_features]
data_make = pd.read_csv('df_cat_make_value.csv')

@app.route('/')
def home():
    # Get unique 'make' values from the cars_data DataFrame
    unique_makes = cars_data['make'].unique()
    return render_template('index.html', unique_makes=unique_makes)
@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        try:
            # Get user input from the form
            hp = float(request.form['hp'])
            cylinders = int(request.form['cylinders'])
            year = int(request.form['year'])
            doors = float(request.form['doors'])
            make = request.form['make']
            transmission = request.form['transmission']

            # Prepare categorical data (perform one-hot encoding)
            make_columns = [col for col in data_make.columns if col.startswith('make_')]  # Get all 'make' columns
            transmission_colum = ['transmission_AUTOMATED_MANUAL','transmission_AUTOMATIC','transmission_MANUAL']

            categorical_data_transmission = pd.DataFrame(0, index=np.arange(1), columns=transmission_colum)
            categorical_data_transmission['transmission_' + transmission] = 1
            # Create a new DataFrame with all 'make' columns and set the selected make to 1 and others to 0
            categorical_data_encoded = pd.DataFrame(0, index=np.arange(1), columns=make_columns)
            categorical_data_encoded['make_' + make] = 1
            print(make_columns)
            # Combine numerical and encoded categorical features
            input_features = pd.concat([
                pd.DataFrame({'hp': [hp], 'cylinders': [cylinders], 'year': [year], 'doors': [doors]}),
                categorical_data_encoded,categorical_data_transmission], axis=1)
            print(input_features)

            # Make a prediction using the loaded model
            prediction = model.predict(input_features)

            # Render HTML template with prediction and input features
            return render_template('prediction_result.html', hp=hp, cylinders=cylinders,
                                   year=year, doors=doors,make=make,transmission=transmission, prediction=round(prediction[0], 2))

        except Exception as e:
            # Handle exceptions or errors here
            print(str(e))
            return jsonify({'error': 'An error occurred during prediction.'})



@app.route('/plot')
def plot():
    def generate_plot_div():
        # Generate Plotly figures
        fig1 = px.scatter(cars_data, x='doors', y='price', color='doors')
        fig1.update_layout(width=400, height=400, title="Scatter Plot Price vs Doors")
        div_fig1 = fig1.to_html(full_html=False)

        fig2 = px.scatter(cars_data, x='cylinders', y='price', color='cylinders')
        fig2.update_layout(width=400, height=400,title="Scatter Plot Price vs cylinders")
        div_fig2 = fig2.to_html(full_html=False)

        fig3 = px.scatter(cars_data, x='hp', y='price')
        fig3.update_layout(width=400, height=400,title="Scatter Plot Price vs hp")
        div_fig3 = fig3.to_html(full_html=False)

        return div_fig1, div_fig2, div_fig3

    def generate_base64_image():
        correlation_matrix = subset_data.corr()

        plt.figure(figsize=(10, 8))
        heatmap = sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5,
                               annot_kws={"size": 10})
        plt.title('Correlation Matrix', fontsize=14)
        plt.xlabel('Features', fontsize=12)
        plt.ylabel('Features', fontsize=12)
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)
        plt.tight_layout()
        plt.savefig('correlation_matrix.png')
        plt.close()

        with open('correlation_matrix.png', 'rb') as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

        return img_base64

    div_fig1, div_fig2, div_fig3 = generate_plot_div()
    img_base64 = generate_base64_image()

    return render_template('dashboard.html', div_fig1=div_fig1, div_fig2=div_fig2, div_fig3=div_fig3, img_base64=img_base64)


if __name__ == '__main__':
    app.run(debug=True)
