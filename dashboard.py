import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="Music Money Analytics", layout="wide")

st.title("🎵 Artist vs. Channel Wealth Dashboard")
st.markdown("""
This tool simulates the financial reality of the music industry.  
Adjust the assumptions in the sidebar to see how **Ownership vs. Flat Fees** changes the numbers.
""")

# --- SIDEBAR: SETUP ---
st.sidebar.header("1. Upload Data")
st.sidebar.info("💡 TIP: Upload BOTH your 'History Log' and 'Detailed Analytics' files together for the best results!")

uploaded_files = st.sidebar.file_uploader(
    "Upload CSV files", 
    type=["csv"], 
    accept_multiple_files=True
)

st.sidebar.markdown("---")
st.sidebar.header("2. Global Assumptions")
rpm = st.sidebar.slider("RPM ($ per 1k views)", 0.5, 10.0, 4.0, 0.1, help="Revenue Per Mille: How much YouTube pays for every 1,000 views.")
flat_fee = st.sidebar.number_input("Avg Flat Fee Paid to Artist ($)", value=3000, step=500, help="The estimated amount the channel owner paid the artist to buy the video rights.")
prod_cost = st.sidebar.number_input("Avg Production Cost per Video ($)", value=2000, step=500, help="How much it costs to make the video (Director, Camera, Editing).")

st.sidebar.markdown("---")
st.sidebar.header("3. Deal Structure (The Pitch)")
platform_cut = st.sidebar.slider("Your Platform Cut (%)", min_value=0, max_value=50, value=10, step=1, help="The percentage YOU take in the proposed deal.")
artist_cut_pct = 100 - platform_cut

st.sidebar.markdown("---")
st.sidebar.header("4. Ghost Income Settings")
ghost_years = st.sidebar.slider("Years until 'Old'", 
                                min_value=0.5, max_value=10.0, value=2.0, step=0.5,
                                help="Videos older than this number of years are considered 'Ghost Income' sources.")
ghost_days = ghost_years * 365 

# --- CONFIG: EXCLUSION LISTS ---
EXCLUDED_KEYWORDS = ['ethiopian', 'ethiopia', 'amharic', 'oromo', 'tigray', 'wolayta', 'hope music']
DROP_CHANNELS = [
    'Liham Melody', 'Hope Music Ethiopia', 'Minew Shewa Tube',
    'Fana Television', 'EBS TV', 'Propictures', 'Merih Media', 
    'Cinemax Entertainment', 'Habesha Music', 'ADMAS MUSIC'
]

# --- INTELLIGENT DATA LOADER ---
if not uploaded_files:
    st.warning("👈 Please upload your CSV file(s) in the sidebar to begin.")
    st.stop()

# Placeholders
df_static = pd.DataFrame()
df_history = pd.DataFrame()
artist_map = {}

for file in uploaded_files:
    try:
        temp_df = pd.read_csv(file, on_bad_lines='skip')
    except:
        file.seek(0)
        temp_df = pd.read_csv(file)
    
    cols = temp_df.columns.tolist()
    
    if 'Date_Scraped' in cols:
        # === HISTORY LOG ===
        df_history = temp_df.copy()
        df_history['Date_Scraped'] = pd.to_datetime(df_history['Date_Scraped'], errors='coerce')
        df_history = df_history.dropna(subset=['Date_Scraped'])
        df_history = df_history.rename(columns={
            'Video_Title': 'Video Title', 'View_Count': 'View Count', 'Channel_Name': 'Channel Name'
        })
        
        if 'Channel Name' in df_history.columns:
            df_history = df_history[~df_history['Channel Name'].isin(DROP_CHANNELS)]
            
        def is_clean_content(title):
            if not isinstance(title, str): return True
            t_lower = title.lower()
            for k in EXCLUDED_KEYWORDS:
                if k in t_lower: return False
            return True

        df_history = df_history[df_history['Video Title'].apply(is_clean_content)]
        st.sidebar.success(f"✅ Loaded History Log ({len(df_history)} rows)")
        
    elif 'Clean_Artist_Name' in cols:
        # === DETAILED ANALYSIS ===
        df_static = temp_df.copy()
        artist_map = df_static.drop_duplicates('Video Title').set_index('Video Title')['Clean_Artist_Name'].to_dict()
        st.sidebar.success(f"✅ Loaded Artist Analysis ({len(df_static)} rows)")

# Merge Logic
if not df_history.empty:
    if artist_map:
        df_history['Clean_Artist_Name'] = df_history['Video Title'].map(artist_map)
        df_history['Is_Identified'] = df_history['Clean_Artist_Name'].notna()
        df_history['Clean_Artist_Name'] = df_history['Clean_Artist_Name'].fillna(df_history['Channel Name'])
    elif 'Clean_Artist_Name' not in df_history.columns:
        df_history['Clean_Artist_Name'] = df_history.get('Channel Name', 'Unknown')
        df_history['Is_Identified'] = False
else:
    df_history['Is_Identified'] = False

# Primary Selection
if not df_static.empty:
    df = df_static.copy()
elif not df_history.empty:
    latest_date = df_history['Date_Scraped'].max()
    df = df_history[df_history['Date_Scraped'] == latest_date].copy()
else:
    st.error("Could not process files.")
    st.stop()

# Smart Column Mapper
possible_date_cols = ['Published At', 'publishedAt', 'Release Date', 'release_date']
for col in possible_date_cols:
    if col in df.columns:
        df = df.rename(columns={col: 'Video Release Date'})
        break

if 'Clean_Artist_Name' not in df.columns:
     df['Clean_Artist_Name'] = df.get('Channel Name', 'Unknown')

# --- ARTIST FILTER ---
st.sidebar.markdown("---")
st.sidebar.header("5. Filter Data")

hide_unidentified = st.sidebar.checkbox("Hide Unidentified (Channels)", value=False, help="Hides rows where we couldn't find a specific Artist Name.")

all_artists = sorted(df['Clean_Artist_Name'].unique().astype(str))
selected_artists = st.sidebar.multiselect("Include Specific Artist(s):", options=all_artists, default=None)
excluded_artists = []
if not selected_artists:
    excluded_artists = st.sidebar.multiselect("Exclude Specific Artist(s):", options=all_artists, default=None)

# Apply Filters
if hide_unidentified and 'Is_Identified' in df_history.columns:
    df_history = df_history[df_history['Is_Identified'] == True]

if selected_artists:
    df = df[df['Clean_Artist_Name'].isin(selected_artists)]
    if not df_history.empty:
        df_history = df_history[df_history['Clean_Artist_Name'].isin(selected_artists)]
    st.sidebar.success(f"Showing {len(selected_artists)} selected artist(s).")
elif excluded_artists:
    df = df[~df['Clean_Artist_Name'].isin(excluded_artists)]
    if not df_history.empty:
        df_history = df_history[~df_history['Clean_Artist_Name'].isin(excluded_artists)]
    st.sidebar.info(f"Showing ALL artists except {len(excluded_artists)} excluded.")
else:
    st.sidebar.info("Showing ALL artists.")

# --- CALCULATIONS ---
df['Actual_Revenue'] = (df['View Count'] / 1000) * rpm
df['Outcome'] = df['Actual_Revenue'].apply(lambda x: 'Artist Lost Money (Hit Song)' if x > flat_fee else 'Artist Won (Safe)')

artist_stats = df.groupby('Clean_Artist_Name').agg({
    'View Count': 'sum', 'Video Title': 'count', 'Actual_Revenue': 'sum'
}).reset_index()

artist_stats['Est_Fees_Received'] = artist_stats['Video Title'] * flat_fee
artist_stats['Total_Prod_Cost'] = artist_stats['Video Title'] * prod_cost
artist_stats['Net_Independent_Profit'] = artist_stats['Actual_Revenue'] - artist_stats['Total_Prod_Cost']
artist_stats['Wealth_Gap'] = artist_stats['Net_Independent_Profit'] - artist_stats['Est_Fees_Received']

# --- TABS ---
tabs = st.tabs([
    "📊 The Asset Gap", 
    "🎟️ The Lottery Ticket", 
    "👻 Ghost Income", 
    "🔮 Deal Simulator", 
    "📈 Weekly Pitch", 
    "📅 Monthly Salary", 
    "🔥 Perfect Timing"
])

# === TAB 1: ASSET GAP ===
with tabs[0]:
    st.header("Who owns the wealth?")
    with st.expander("ℹ️ How is this calculated?"):
        st.markdown(f"""
        **The Logic:**
        We compare the total 'Net Profit' if the artist had been independent versus what they actually got paid.
        
        **1. Independent Scenario (Net Profit):**
        * Formula: `(Total Views / 1,000 * ${rpm} RPM) - (Number of Videos * ${prod_cost} Production Cost)`
        * This assumes the artist pays for their own video production but keeps all revenue.
        
        **2. Current Reality (Flat Fees):**
        * Formula: `Number of Videos * ${flat_fee} Flat Fee`
        * This assumes the artist sold every video for the average fee you set in the sidebar.
        
        **3. The Wealth Gap:**
        * Formula: `Independent Net Profit - Flat Fees Received`
        """)

    top_artists = artist_stats.sort_values('Actual_Revenue', ascending=False).head(15)
    fig_gap = go.Figure()
    fig_gap.add_trace(go.Bar(y=top_artists['Clean_Artist_Name'], x=top_artists['Net_Independent_Profit'], name='Potential Net Profit', orientation='h', marker_color='#EF553B'))
    fig_gap.add_trace(go.Bar(y=top_artists['Clean_Artist_Name'], x=top_artists['Est_Fees_Received'], name='Actual Fees Received', orientation='h', marker_color='#00CC96'))
    fig_gap.update_layout(barmode='overlay', title="The Asset Gap", height=600, legend=dict(orientation="h", y=1.02, x=0.3))
    st.plotly_chart(fig_gap, use_container_width=True)
    
    gap = artist_stats['Wealth_Gap'].sum()
    if gap > 0:
        st.error(f"💸 **Total Opportunity Cost: ${gap:,.0f}**")
        st.write("Interpretation: This is the **'Missing Wealth'**. Money left on the table by selling rights.")
    else:
        st.success(f"✅ **Total Value Saved: ${abs(gap):,.0f}**")
        st.write("Interpretation: The artists **won** this deal. They collected more in fees than the videos earned.")

# === TAB 2: LOTTERY ===
with tabs[1]:
    st.header("Did selling for a Flat Fee pay off?")
    with st.expander("ℹ️ How is this calculated?"):
        st.markdown(f"""
        **The Logic:**
        We analyze every single video individually to see if the Flat Fee was a 'Good Deal' or a 'Bad Deal'.
        
        * **Formula:** `(Video Views / 1,000) * ${rpm} RPM`
        * **The Threshold:** We compare the result against your Flat Fee of **${flat_fee}**.
        
        🔴 **Red Dot (Artist Lost):** The video earned MORE than ${flat_fee}. The artist shouldn't have sold it.
        🟢 **Green Dot (Artist Won):** The video earned LESS than ${flat_fee}. The artist made a smart choice selling it.
        """)

    df_chart = df[df['View Count'] > 10000].copy()
    if not df_chart.empty and 'Video Release Date' in df_chart.columns:
        fig_scatter = px.scatter(df_chart, x='Video Release Date', y='Actual_Revenue', color='Outcome', 
                               hover_data=['Video Title', 'Clean_Artist_Name'], 
                               color_discrete_map={'Artist Lost Money (Hit Song)': '#EF553B', 'Artist Won (Safe)': '#00CC96'}, 
                               title="Revenue per Video vs. Release Date")
        fig_scatter.add_hline(y=flat_fee, line_dash="dash", annotation_text=f"Flat Fee (${flat_fee})")
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Scatter plot requires 'Video Release Date' or 'Published At'.")

# === TAB 3: GHOST INCOME ===
with tabs[2]:
    st.header(f"👻 Ghost Income (Videos > {ghost_years} Years Old)")
    with st.expander("ℹ️ How is this calculated?"):
        st.markdown(f"""
        **The Logic:**
        "Ghost Income" is the passive money old videos make *right now*, which the artist usually forfeits when they sell the rights.
        
        **1. The Filter:**
        * Video must be older than **{ghost_years} years** (older than {ghost_days} days).
        * Video must be getting significant daily views (>100).
        
        **2. The Calculation:**
        * `Daily Views * 365 Days * (${rpm} RPM / 1000)`
        """)

    if 'Video Release Date' in df.columns and 'Avg_Daily_Views' in df.columns:
        # Calculate Age
        df['Video Release Date'] = pd.to_datetime(df['Video Release Date'])
        df['Days_Since_Release'] = (pd.Timestamp.now() - df['Video Release Date']).dt.days
        
        old_gold = df[(df['Days_Since_Release'] > ghost_days) & (df['Avg_Daily_Views'] > 100)].copy()
        if not old_gold.empty:
            old_gold['Est_Annual_Passive'] = (old_gold['Avg_Daily_Views'] * 365 / 1000) * rpm
            fig_ghost = px.bar(old_gold.sort_values('Est_Annual_Passive', ascending=False).head(15), x='Est_Annual_Passive', y='Video Title', color='Clean_Artist_Name', orientation='h')
            st.plotly_chart(fig_ghost, use_container_width=True)
            st.success(f"💰 Total Passive Income: **${old_gold['Est_Annual_Passive'].sum():,.0f} / year**")
        else:
            st.warning("No videos fit the Ghost Income criteria.")
    else:
        st.warning("Missing data for Ghost Income. Use the Detailed Analysis file.")

# === TAB 4: DEAL SIMULATOR ===
with tabs[3]:
    st.header("🔮 Should I sign this contract?")
    with st.expander("ℹ️ How does this work?"):
        st.markdown(f"""
        **The Logic:**
        We use the artist's historical data to predict if a *new* deal is worth signing.
        
        **1. The Prediction:**
        * We look at the **Median View Count** of the artist's past videos (filtering out the ones you uncheck).
        * We calculate projected revenue: `(Median Views / 1000) * ${rpm} RPM`.
        
        **2. The Comparison:**
        * **Scenario A (Sign):** You get the Flat Fee cash guaranteed.
        * **Scenario B (Independent):** You get the Projected Revenue minus your Production Cost.
        """)

    c1, c2 = st.columns(2)
    offer = c1.number_input("They are offering (Flat Fee):", value=5000, step=500)
    cost = c1.number_input("My Production Cost:", value=2500, step=500)
    target = c2.selectbox("Select Artist:", options=all_artists)
    
    st.markdown("---")
    t_data = df[df['Clean_Artist_Name'] == target].copy()
    if not t_data.empty:
        d_data = t_data[['Video Title', 'View Count']].copy()
        d_data.insert(0, "Include", True)
        edited = st.data_editor(d_data, hide_index=True, height=250)
        sel = edited[edited['Include']]['Video Title'].tolist()
        clean = t_data[t_data['Video Title'].isin(sel)]
        
        if not clean.empty:
            med_views = clean['View Count'].median()
            rev = (med_views / 1000) * rpm
            prof = rev - cost
            
            x1, x2 = st.columns(2)
            x1.info(f"📝 Deal: **${offer:,.0f}** guaranteed")
            x2.metric("🚀 Independent Net Profit", f"${prof:,.0f}", delta=f"{prof - offer:,.0f}")
            
            diff = prof - offer
            if diff > 1000: st.error("❌ **REJECT.** You make more money alone.")
            elif diff < -1000: st.success("✅ **TAKE IT.** Good deal.")
            else: st.warning("⚠️ **TOSSUP.** Fair deal.")

# === TAB 5: WEEKLY PITCH ===
with tabs[4]:
    if not df_history.empty:
        st.header("📈 The Weekly Pulse (Your Pitch Tool)")
        with st.expander("ℹ️ How is this calculated?"):
             st.markdown(f"""
             **The Logic:**
             This tab calculates the growth between your two most recent history logs to show *current* velocity.
             
             **1. Revenue Calculation:**
             * `Views Gained This Week / 1000 * ${rpm} RPM`
             
             **2. The Proposal Split:**
             * We calculate your cut based on the **{platform_cut}%** fee set in the Sidebar.
             * **Artist Keeps:** {artist_cut_pct}% of the revenue.
             * **Platform Keeps:** {platform_cut}% of the revenue.
             """)

        dates = sorted(df_history['Date_Scraped'].unique())
        if len(dates) < 2:
            st.warning("⚠️ Need at least 2 weekly logs to calculate growth.")
        else:
            latest, prev = dates[-1], dates[-2]
            idx = 'Video_ID' if 'Video_ID' in df_history.columns else 'Video Title'
            
            df_latest = df_history[df_history['Date_Scraped'] == latest].drop_duplicates(idx).set_index(idx)
            df_prev = df_history[df_history['Date_Scraped'] == prev].drop_duplicates(idx).set_index(idx)
            
            df_growth = df_latest.join(df_prev, lsuffix='_now', rsuffix='_prev')
            df_growth['Views_Gained'] = df_growth['View Count_now'] - df_growth['View Count_prev']
            
            # Metrics
            gained = df_growth['Views_Gained'].sum()
            rev_week = (gained / 1000) * rpm
            
            st.subheader(f"📅 Performance: {pd.to_datetime(prev).strftime('%b %d')} vs {pd.to_datetime(latest).strftime('%b %d')}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Views Gained (Last 7 Days)", f"+{gained:,.0f}")
            c2.metric("Revenue Generated (Last 7 Days)", f"${rev_week:,.2f}")
            c3.metric("Projected Monthly Income", f"${rev_week * 4:,.2f}", help="Weekly Revenue x 4")
            
            st.markdown("---")
            
            # THE PITCH
            st.subheader("🤝 The 'Independent Platform' Proposal")
            st.info(f"Using Deal Structure from Sidebar: **You Keep {artist_cut_pct}%** | **Platform Takes {platform_cut}%**")
            
            p1, p2 = st.columns(2)
            
            # Current
            p1.warning("❌ Current Status Quo (Selling Rights)")
            p1.markdown(f"* You earned: **$0.00** this week.\n* Channel Owner kept: **${rev_week:,.2f}**")
            
            # New
            my_cut_amt = rev_week * (platform_cut / 100.0)
            artist_cut_amt = rev_week * (artist_cut_pct / 100.0)
            
            p2.success(f"✅ With Us ({artist_cut_pct}/{platform_cut} Split)")
            p2.markdown(f"""
            * **You Keep ({artist_cut_pct}%):** <span style='font-size: 24px; font-weight: bold;'>${artist_cut_amt:,.2f}</span> / week
            * **We Take ({platform_cut}%):** ${my_cut_amt:,.2f}
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Growth Charts
            st.subheader("🔥 Top Performing Videos (Last Week)")
            df_growth['Week_Revenue'] = (df_growth['Views_Gained'] / 1000) * rpm
            top = df_growth.sort_values('Views_Gained', ascending=False).head(10)
            if not top.empty:
                fig = px.bar(top, x='Week_Revenue', y='Video Title_now' if 'Video Title_now' in top.columns else top.index, orientation='h', text_auto='$.2f')
                st.plotly_chart(fig, use_container_width=True)
            
            # Velocity
            st.subheader("📈 Velocity: Views Gained Over Time")
            daily_agg = df_history.groupby(['Date_Scraped', 'Clean_Artist_Name'])['View Count'].sum().reset_index()
            daily_agg = daily_agg.sort_values('Date_Scraped')
            daily_agg['Previous_Views'] = daily_agg.groupby('Clean_Artist_Name')['View Count'].shift(1)
            daily_agg['New_Views'] = daily_agg['View Count'] - daily_agg['Previous_Views']
            
            velocity_data = daily_agg.dropna(subset=['New_Views'])
            if not velocity_data.empty:
                fig_vel = px.line(velocity_data, x='Date_Scraped', y='New_Views', color='Clean_Artist_Name', markers=True, title="Growth Velocity (New Views per Week)")
                st.plotly_chart(fig_vel, use_container_width=True)
    else:
        st.warning("Please upload a History Log file to see Weekly Cashflow.")

# === TAB 6: MONTHLY SALARY SIM ===
with tabs[5]:
    st.header("📅 Monthly Salary Simulator")
    st.markdown("##### The Argument: *'Here is the paycheck you missed.'*")
    
    with st.expander("ℹ️ How does this work?"):
        st.markdown(f"""
        **The Logic:**
        We simulate a monthly paycheck based on the artist's last 5 videos.
        
        **1. Gross Revenue:**
        * `Daily Views * 30 Days * (${rpm} RPM / 1000)`
        
        **2. The Deduction (Platform Fee):**
        * We automatically deduct your **{platform_cut}%** platform fee set in the Sidebar.
        * **Net Pay:** What the artist actually takes home.
        """)

    salary_artist = st.selectbox("Select Artist for Payroll:", options=all_artists, key="salary_artist")
    
    s_data = df[df['Clean_Artist_Name'] == salary_artist].copy()
    
    if not s_data.empty and 'Video Release Date' in s_data.columns:
        s_data['Video Release Date'] = pd.to_datetime(s_data['Video Release Date'])
        recent_videos = s_data.sort_values('Video Release Date', ascending=False).head(5)
        
        if not recent_videos.empty and 'Avg_Daily_Views' in recent_videos.columns:
            # 1. Gross Revenue
            recent_videos['Gross_Monthly'] = (recent_videos['Avg_Daily_Views'] * 30 / 1000) * rpm
            
            # 2. Apply Platform Cut (From Sidebar)
            recent_videos['Net_Monthly_Pay'] = recent_videos['Gross_Monthly'] * (artist_cut_pct / 100.0)
            
            st.subheader(f"Projected Monthly Checks for {salary_artist}")
            st.caption(f"Calculated using a **{artist_cut_pct}% Split** (You keep {artist_cut_pct}%).")
            
            pay_stub = recent_videos[['Video Title', 'Video Release Date', 'Avg_Daily_Views', 'Net_Monthly_Pay']].copy()
            pay_stub['Video Release Date'] = pay_stub['Video Release Date'].dt.date
            
            st.dataframe(pay_stub.style.format({'Net_Monthly_Pay': '${:,.2f}', 'Avg_Daily_Views': '{:,.0f}'}), use_container_width=True)
            
            total_monthly = pay_stub['Net_Monthly_Pay'].sum()
            annual_salary = total_monthly * 12
            
            c1, c2 = st.columns(2)
            c1.metric("Your Total Monthly Salary (Net)", f"${total_monthly:,.2f}")
            c2.metric("Annual Run Rate (Net)", f"${annual_salary:,.2f}")
            
            st.info(f"💡 **Reality Check:** If you were on our platform today, you would be receiving a check for **${total_monthly:,.0f} per month** (after our {platform_cut}% fee).")
        else:
            st.warning("No recent videos found with daily view data.")
    else:
        st.warning("Need 'Video Release Date' column. Upload Detailed Analytics file.")

# === TAB 7: HEATMAP ===
with tabs[6]:
    st.header("🔥 The 'Perfect Timing' Heatmap")
    with st.expander("ℹ️ How does this work?"):
        st.markdown("""
        **The Logic:**
        This heatmap looks at **historical data** to see which release days generate the most views.
        * **Darker Colors:** Higher Median Views (Better performance).
        * **Lighter Colors:** Lower Median Views (Worse performance).
        * Use this to decide when to drop your next video!
        """)

    if 'Video Release Date' in df.columns:
        hm_df = df.copy()
        hm_df['Video Release Date'] = pd.to_datetime(hm_df['Video Release Date'])
        hm_df['Month'] = hm_df['Video Release Date'].dt.month_name()
        hm_df['Day'] = hm_df['Video Release Date'].dt.day_name()
        
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        heatmap_data = hm_df.groupby(['Month', 'Day'])['View Count'].median().reset_index()
        
        fig_heat = px.density_heatmap(
            heatmap_data, 
            x='Month', 
            y='Day', 
            z='View Count', 
            title="Median Views by Release Time",
            category_orders={'Month': month_order, 'Day': day_order},
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.warning("Missing 'Video Release Date'. Upload Detailed Analytics file.")