import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns

# Загрузка данных
# Предположим, что данные загружаются из CSV или базы данных
@st.cache_data
def load_data():
    tickets_demand = pd.read_csv('data/df_demand_06.11.csv')
    tickets_demand['date_departure'] = pd.to_datetime(tickets_demand['date_departure'])
    sales = pd.read_csv('data/df_sales_06.11.csv')
    routes = pd.read_csv('data/df_routes_05.11.csv')
    stations = pd.read_csv('data/df_stations_05.11.csv')
    # Загрузите и другие таблицы аналогично
    return tickets_demand, sales, routes, stations

tickets_demand, sales, routes, stations = load_data()

# Настройка страницы
st.title("Анализ спроса и продаж билетов на поезда")
st.sidebar.title("Навигация")

# Сайдбар для выбора разделов
section = st.sidebar.selectbox("Выберите раздел", 
                               ["Обзор данных", "Спрос на билеты", "Продажи билетов"])

### Обзор данных
if section == "Обзор данных":
    st.header("Обзор данных")
    table = st.selectbox("Выберите таблицу для просмотра", 
                         ["tickets_demand", "sales", "routes", "stations"])

    # Добавляем выбор года для таблиц tickets_demand и sales
    if table in ["tickets_demand", "sales"]:
        year_option = st.selectbox("Выберите год", ["Все годы", 2020, 2021, 2022, 2023])

    if table == "tickets_demand":
        # Фильтрация данных по выбранному году
        filtered_data = tickets_demand
        if year_option != "Все годы":
            filtered_data = tickets_demand[tickets_demand['date_departure'].dt.year == year_option]
        
        st.write(filtered_data)
        
    elif table == "sales":
        # Фильтрация данных по выбранному году
        filtered_data = sales
        if year_option != "Все годы":
            filtered_data = sales[pd.to_datetime(sales['departure_datetime']).dt.year == year_option]
        
        st.write(filtered_data.head(100))

    elif table == "routes":
        st.write(routes)
        
    elif table == "stations":
        st.write(stations)

# Спрос на билеты
elif section == "Спрос на билеты":
    st.header("Анализ спроса на билеты")
    st.write("Выберите параметры для анализа")

    # Фильтр по году
    year_option = st.selectbox("Выберите год", ["Все годы", 2020, 2021, 2022, 2023])

    # Фильтры по станциям отправления и назначения с опцией "Все направления"
    origin_options = ["Все направления"] + list(tickets_demand['origin'].unique())
    destination_options = ["Все направления"] + list(tickets_demand['destination'].unique())
    origin = st.selectbox("Станция отправления", origin_options)
    destination = st.selectbox("Станция назначения", destination_options)

    # Применение фильтров к данным
    filtered_data = tickets_demand
    if origin != "Все направления":
        filtered_data = filtered_data[filtered_data['origin'] == origin]
    if destination != "Все направления":
        filtered_data = filtered_data[filtered_data['destination'] == destination]

    # Фильтрация по году
    if year_option != "Все годы":
        filtered_data = filtered_data[filtered_data['date_departure'].dt.year == year_option]

    if not filtered_data.empty:
        st.write(filtered_data)

        # 1. Линейный график спроса по дате
        line_fig = px.line(
            filtered_data, 
            x='date_departure', 
            y='demand', 
            title="Спрос на билеты по дате отправления",
            labels={'date_departure': 'Дата отправления', 'demand': 'Спрос'}
        )
        line_fig.update_layout(xaxis_title="Дата отправления", yaxis_title="Спрос")
        st.plotly_chart(line_fig)

        # 2. Столбчатая диаграмма спроса по месяцам
        filtered_data['month'] = filtered_data['date_departure'].dt.month
        month_labels = {
            1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
            7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
        }
        filtered_data['month_name'] = filtered_data['month'].map(month_labels)

        bar_fig = px.bar(
            filtered_data, 
            x='month_name', 
            y='demand', 
            title="Спрос на билеты по месяцам",
            labels={'month_name': 'Месяц', 'demand': 'Спрос'},
            category_orders={"month_name": list(month_labels.values())}
        )
        bar_fig.update_layout(xaxis_title="Месяц", yaxis_title="Спрос")
        st.plotly_chart(bar_fig)

        # 3. Scatter plot для анализа по выбранной оси X
        scatter_options = [col for col in filtered_data.columns if col not in ['demand', 'date_departure']]
        selected_x = st.selectbox("Выберите столбец для оси X", scatter_options)

        scatter_fig = px.scatter(
            filtered_data,
            x=selected_x,
            y='demand',
            title=f"Зависимость спроса от {selected_x}",
            labels={selected_x: selected_x, 'demand': 'Спрос'}
        )
        scatter_fig.update_traces(marker=dict(size=6, opacity=0.7))
        scatter_fig.update_layout(xaxis_title=selected_x, yaxis_title="Спрос")
        st.plotly_chart(scatter_fig)

        # 4. Корреляционная матрица
        st.header("Корреляционная матрица")
        correlation_data = filtered_data.drop(columns=['demand', 'date_departure', 'week_day', 'month', 'month_name', 'origin', 'destination'], errors='ignore')
        correlation_matrix = correlation_data.corr()
        
        fig_corr, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", center=0, ax=ax)
        ax.set_title("Корреляционная матрица")
        st.pyplot(fig_corr)

        # 5. Торнадо-диаграмма влияния параметров на demand
        st.header("Торнадо-диаграмма влияния параметров на спрос")
        
        # Используем абсолютные значения корреляций, чтобы увидеть силу связи
        correlation_with_demand = filtered_data.drop(columns=['date_departure', 'week_day', 'month', 'month_name', 'origin', 'destination']).corr()['demand'].drop('demand').abs().sort_values(ascending=False)
        fig_tornado = go.Figure(go.Bar(
            x=correlation_with_demand.values,
            y=correlation_with_demand.index,
            orientation='h',
            marker=dict(color='skyblue')
        ))
        fig_tornado.update_layout(
            title="Влияние параметров на спрос",
            xaxis_title="Абсолютное значение корреляции",
            yaxis_title="Параметр",
            yaxis=dict(categoryorder='total ascending')
        )
        st.plotly_chart(fig_tornado)

    else:
        st.write("Нет данных для выбранных фильтров.")

# Продажи билетов
elif section == "Продажи билетов":
    st.header("Анализ продаж билетов")

    # Преобразуем даты в формат datetime для фильтрации по году
    sales['departure_datetime'] = pd.to_datetime(sales['departure_datetime'])
    
    # Фильтры по станциям отправления и назначения с опцией "Все направления"
    origin_options = ["Все направления"] + list(sales['origin'].unique())
    destination_options = ["Все направления"] + list(sales['destination'].unique())
    origin = st.selectbox("Станция отправления", origin_options)
    destination = st.selectbox("Станция назначения", destination_options)

    # Фильтр по году
    year_option = st.selectbox("Выберите год", ["Все годы", 2020, 2021, 2022, 2023])

    # Применение фильтров к данным
    filtered_sales = sales
    if origin != "Все направления":
        filtered_sales = filtered_sales[filtered_sales['origin'] == origin]
    if destination != "Все направления":
        filtered_sales = filtered_sales[filtered_sales['destination'] == destination]
    if year_option != "Все годы":
        filtered_sales = filtered_sales[filtered_sales['departure_datetime'].dt.year == year_option]

    if not filtered_sales.empty:
        st.write(filtered_sales.head(100))

        # 1. Scatter plot или круговая диаграмма для анализа продаж по выбранной оси X
        scatter_options = [col for col in filtered_sales.columns if col not in ['ticket_number', 'order_number',
                                                                                'various_fees', 'train',
                                                                                'user', 'base fare']]
        selected_x = st.selectbox("Выберите столбец для оси X", scatter_options)

        # Группировка по выбранному признаку и подсчёт количества проданных билетов
        grouped_sales = filtered_sales.groupby(selected_x).size().reset_index(name='ticket_count')

        # Определяем количество уникальных значений в выбранной колонке
        unique_values = grouped_sales[selected_x].nunique()

        if unique_values > 10:
            # Отрисовка scatter plot, если значений больше 10
            scatter_fig = px.scatter(
                grouped_sales,
                x=selected_x,
                y='ticket_count',
                title=f"Количество проданных билетов по {selected_x}",
                labels={selected_x: selected_x, 'ticket_count': 'Количество проданных билетов'}
            )
            scatter_fig.update_traces(marker=dict(size=6, opacity=0.7))
            scatter_fig.update_layout(xaxis_title=selected_x, yaxis_title="Количество проданных билетов")
            st.plotly_chart(scatter_fig)

        else:
            # Отрисовка круговой диаграммы, если значений от 2 до 10
            pie_fig = px.pie(
                grouped_sales,
                names=selected_x,
                values='ticket_count',
                title=f"Доля продаж по {selected_x}"
            )
            st.plotly_chart(pie_fig)

        # 2. Графики зависимости цены от других переменных
        # Фильтры для выбора столбцов для построения графиков
        cols_to_drop = ['ticket_number', 'order_number', 'various_fees', 'train', 'user', 'base fare']
        numerical_cols = filtered_sales.drop(columns=cols_to_drop).select_dtypes(include=['float64', 'int64']).columns.tolist()
        categorical_cols = filtered_sales.drop(columns=cols_to_drop).select_dtypes(include=['object']).columns.tolist()

        # Выбор столбца для оси X и Y
        selected_x = st.selectbox("Выберите столбец для оси X", numerical_cols + categorical_cols)
        selected_y = 'price'

        # 2. Построение графика зависимости
        if selected_x in numerical_cols:
            # Scatter plot для числовых данных
            st.subheader(f"График зависимости {selected_y} от {selected_x}")
            fig, ax = plt.subplots()
            ax.scatter(filtered_sales[selected_x], filtered_sales[selected_y], alpha=0.5)
            ax.set_xlabel(selected_x)
            ax.set_ylabel(selected_y)
            ax.set_title(f"Зависимость {selected_y} от {selected_x}")
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
            st.pyplot(fig)

        else:
            # Boxplot для категориальных и числовых данных
            st.subheader(f"График зависимости {selected_y} по категориям {selected_x}")
            fig, ax = plt.subplots()
            sns.boxplot(data=filtered_sales, x=selected_x, y=selected_y, ax=ax)
            ax.set_title(f"Зависимость {selected_y} по {selected_x}")
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
            st.pyplot(fig)

        # elif selected_x in numerical_cols and selected_y in categorical_cols:
        #     # Boxplot для числовых и категориальных данных
        #     st.subheader(f"График зависимости {selected_x} по категориям {selected_y}")
        #     fig, ax = plt.subplots()
        #     sns.boxplot(data=filtered_sales, x=selected_y, y=selected_x, ax=ax)
        #     ax.set_title(f"Зависимость {selected_x} по {selected_y}")
        #     st.pyplot(fig)

    else:
        st.write("Нет данных для выбранных фильтров.")


# ### Маршруты
# elif section == "Маршруты":
#     st.header("Анализ маршрутов")

#     if not routes.empty:
#         st.write(routes)

#         # Карта расстояний
#         fig, ax = plt.subplots(figsize=(12, 8))
#         sns.barplot(x=routes['od_name'], y=routes['distance'], ax=ax)
#         ax.set_title("Дистанция по маршрутам")
#         ax.set_xticklabels(ax.get_xticklabels(), rotation=90, fontsize=8)
#         st.pyplot(fig)
