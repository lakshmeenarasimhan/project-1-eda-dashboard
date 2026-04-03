# import 
import streamlit  as st
import pandas as pd
import numpy as np
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Bangalore Restaurant Analysis",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",            
    menu_items={                                 
        'About': "My Zomato Analysis App"
    }
)

# Title
st.title("Bangalore Restaurant Analysis")
st.markdown("*An exploratory analysis of 41,000+ restaurants in Bangalore using Zomato data*")

st.markdown("""
> 💡 **How to use:** Use the filters on the left sidebar to explore 
> restaurants by location, cuisine, price and rating. 
> Charts update automatically!
""")

#load cache
@st.cache_data
def load_data():
    return pd.read_csv("data/cleaned/zomato_cleaned.csv")

df = load_data()

#Sidebar
st.sidebar.header("Filters")

df_filtered = df.copy()

all_loc = sorted(df['location'].unique())
selected_loc = st.sidebar.multiselect(
    "Select Locations",
    options= all_loc,
    default=[]
)

online_ord = st.sidebar.selectbox(
    "Online Order",
    options= ['All','Yes','No']
)

rate_range = st.sidebar.slider(
    label = "Select rating range",
    min_value = 0.0,
    max_value = 5.0,
    value = (0.0,5.0),
    step = 0.1
)

all_cus = sorted(df['cuisines'].str.split(',').explode().str.strip().unique())
selected_cus = st.sidebar.multiselect(
    "Cuisines",
    options = all_cus,
    default=[]
)

min_cost = float(df['approx_cost(for two people)'].min())
max_cost = float(df['approx_cost(for two people)'].max())
price_range = st.sidebar.slider(
    label = "Select price range",
    min_value= min_cost,
    max_value = max_cost,
    value = (min_cost,max_cost),
    step = 100.0,
)
if selected_loc:
    df_filtered = df[df['location'].isin(selected_loc)]

if online_ord != 'All':
    df_filtered = df_filtered[df_filtered['online_order'] == online_ord]

df_filtered = df_filtered[df_filtered['rate'].between(rate_range[0], rate_range[1])]

if selected_cus:
    joined_cus = '|'.join(selected_cus)
    df_filtered = df_filtered[df_filtered['cuisines'].str.contains(joined_cus,case = False,na = False) ]

df_filtered = df_filtered[df_filtered['approx_cost(for two people)'].between(price_range[0],price_range[1])]

st.write(f"Showing {len(df_filtered)} restaurants")

#KPI cards
if df_filtered.empty:
    st.warning("No restaurants found with these filters! Try adjusting your criteria.")
else:
    total_res = df_filtered['name'].nunique()
    avg_rate = round(df_filtered['rate'].mean(),2)
    top_cusi = df_filtered['cuisines'].mode()[0]
    avg_price = int(df_filtered['approx_cost(for two people)'].mean())

    col1,col2,col3,col4 = st.columns([1,1,2,1])
    with col1:
        st.metric("Total Restaurants",total_res)
    with col2:
        st.metric("Average Ratings",avg_rate,help = "Out of 5.0")
    with col3:
        st.metric("Top Cuisine",top_cusi)
    with col4:
        st.metric("Average Price",avg_price)

# Plotting 
tab1,tab2,tab3 = st.tabs(["Distributions & Trends", "Neighborhood Breakdown", "Hidden Gems"])

with tab1:
    #Plot-1 Distribution of ratings
    st.markdown("### Distribution of Ratings")
    fig_rating = px.histogram(
        data_frame = df_filtered,
        x = 'rate',
        marginal = 'box',
        color_discrete_sequence= ["#EE56F0"] 
    )
    fig_rating.update_traces(marker_line_color = "black",marker_line_width = 1)
    st.plotly_chart(fig_rating,use_container_width = True)

    #Plot-2 Distribution of Restaurent type
    st.markdown("### Distribution of Restaurant Types")
    fig_donut = px.pie(
        data_frame=df_filtered,
        names='listed_in(type)',
        hole=0.5,
        color_discrete_sequence=['#EE56F0', '#D02CD2', '#99149B', '#F18BF4', '#F8BBF9']
    )
    fig_donut.update_traces(textposition='inside', textinfo='percent+label')
    fig_donut.update_layout(showlegend=False)
    st.plotly_chart(fig_donut, use_container_width=True)

with tab2:
    #Dynamic plot
    choice = st.radio(
        label = "Top 10 Ranked By:",
        options = ["Highest Rated","Most Popular(by votes)"],
        horizontal = True
        )
    
    st.markdown(f"### Dynamic plot based on {choice}")
    
    if choice == "Highest Rated":
        top_10 = df_filtered.sort_values(by = 'rate',ascending = False).drop_duplicates(subset=['name']).head(10)
        top_10['name'] = top_10['name'].str[:30]
        y_col = 'rate'
    else :
        top_10 = df_filtered.sort_values(by = 'votes',ascending = False).drop_duplicates(subset=['name']).head(10)
        top_10['name'] = top_10['name'].str[:30]
        y_col = 'votes'

    fig_bar = px.bar(
        data_frame = top_10,
        x = 'name',
        y = y_col,
        color = y_col,
        hover_data=['rate', 'votes'],
        color_continuous_scale= ['#F8BBF9','#99149B']
        )
    
    st.plotly_chart(fig_bar,use_container_width = True)

    #Restaurants with the Most Locations
    st.markdown("### Restaurants with the Most Locations")
    chain_counts = df_filtered['name'].value_counts().head(10).reset_index()
    chain_counts.columns = ['name', 'outlets']
    fig_chains = px.bar(
        data_frame=chain_counts,
        x='outlets',
        y='name',
        color='outlets',
        color_continuous_scale=['#F8BBF9', '#99149B']
    )
    fig_chains.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_chains, use_container_width=True)

with tab3:
    if not selected_loc:
        st.warning("Please select a specific neighborhood from the sidebar to generate the scatter plot!")
    else:
        st.markdown("### Restaurant Value Matrix")
        fig_scatter = px.scatter(
            data_frame = df_filtered,
            x = 'approx_cost(for two people)',
            y = 'rate',
            size = 'votes',
            color = 'location',
            hover_name = 'name',
            size_max = 45,
        )

        fig_scatter.update_traces(
            marker=dict(
                line=dict(width=0), 
                opacity=0.6         
            )
        )
        fig_scatter.update_layout(showlegend=False)

        st.plotly_chart(fig_scatter,use_container_width = True)

        st.markdown("### Statistical Spread of Ratings by Service Type")
        fig_box = px.box(
            data_frame=df_filtered,
            x='listed_in(type)',
            y='rate',
            color='listed_in(type)',
            color_discrete_sequence=['#EE56F0', '#D02CD2', '#99149B', '#F18BF4', '#F8BBF9']
        )
        fig_box.update_layout(showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)


# Key Insights Section
st.markdown("---")
st.header("💡 Key Insights")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    ### Most Surprising Finding
    Cost and rating have only a **weak correlation (0.38)** in Bangalore's 
    restaurant scene — meaning expensive restaurants are NOT guaranteed 
    to be better rated.
    
    > A ₹300 restaurant can easily outrate a ₹2,000 one!
    """)

with col2:
    st.success("""
    ### 🏆 Business Recommendation
    If opening a new restaurant in Bangalore:
    
    📍 **Location** → JP Nagar, Jayanagar or Indiranagar
    
    🍛 **Cuisine** → North Indian + Chinese
    
    📱 **Online Ordering** → Yes
    
    💰 **Price Range** → ₹300 - ₹1,500 for two
    """)

st.warning("""
### ⚠️ Data Limitations
This analysis is based on Zomato listings only and may not represent 
the complete restaurant ecosystem. Additional data needed:
- Individual dish prices
- Separate food vs service ratings  
- Time-based ordering patterns
- Customer demographic data
""")


st.markdown("---")
st.markdown("""
<div style='text-align: center; color: grey;'>
Built by LaKshmeenarasimhan U | Data Source: Zomato Bangalore | 
<a href='https://github.com/yourusername/project-1-eda-dashboard'>
GitHub Repository</a>
</div>
""", unsafe_allow_html=True)