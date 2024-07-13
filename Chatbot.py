# Databricks notebook source
# MAGIC %pip install gradio==3.27.0
# MAGIC %pip install openai

# COMMAND ----------

# dbutils.library.restartPython()

# COMMAND ----------

# from openai import OpenAI
import gradio as gr
import re
import json
import google.generativeai as genai
# from dotenv import load_dotenv
# import os

# load_dotenv()


# Regex to get the url from the model response
regex = "(?P<url>(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-]))"

# Config data
# Path to config file
config_file_path = "config.json"
with open(config_file_path,'r') as cfile:
    config = json.load(cfile)

# API_KEY=os.getenv("AIzaSyCPYjgyNYZrlJHPZ21UHVd5GFCh9ofeCXE")

genai.configure(api_key="AIzaSyCPYjgyNYZrlJHPZ21UHVd5GFCh9ofeCXE")
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])

initial_prompt = '''
I have Tableau dashboards with the following characteristics: {dashboards_tabs_data}.
Based on the descriptions, respond the next prompt with the dashboard that most likely have the information requested. Make sure to include the url in your response so the user can access it but not as a link. If the region or state is mentioned in the question, add '?Region=Central' or '?State=California' to the url so the view can be filtered properly.
Make sure to include the url in your response so the user can access it but not as a link. If the region or state is mentioned in the question, add '?Region=Central' or '?State=California' to the url so the view can be filtered properly.
'''.format(dashboards_tabs_data=config['DashboardsTabs'])

message_history = [initial_prompt]
reply_history=['']

html = None

with gr.Blocks() as demo:
    gr.Markdown(
        """
        # Tableau Dashboard Chatbot
        """
    )
    #     Use natural language to find and access relevant Tableau dashboards.
    #     This demo uses the Public Superstore Dashboard as an example, so you can ask about profits, sales, shippings, orders, etc.
    #     """
    # )
    with gr.Row() as row:
        with gr.Column(scale=10) as col:
            chatbot = gr.Chatbot(height=380)
            msg = gr.Textbox(lines=1)
            clear = gr.Button("Clear")
        with gr.Column(scale=2) as col:
            #Initialize the dashboard area with an empty space
            dashboard = gr.HTML(html)

    def user(user_message, history):
        return "", history + [[user_message, None]]

    def bot(history):
        global message_history
        global reply_history
        message = history[-1][0]
        message_history.append(message)
        tmp=chat.send_message(message_history[0])
        reply_history.append(tmp)
        completion = chat.send_message(message_history[-1])
        reply_content = completion.text
        reply_history.append(reply_content)
        history[-1][1] = reply_content
        return history
    
    def update_dashboard(history):
        global html
        global reply_history
        # chatbot_response = history[-1][1]
        chatbot_response=reply_history[-1]
        filter_strings = []
        for part in chatbot_response.split():
            if 'public.tableau.com' in part:
                url = re.search(regex, part).group("url")
                tableau_url_list = url.split('?')
                tableau_url = tableau_url_list[0]
                if len(tableau_url_list) > 1:
                    for filter in tableau_url_list[1].split('&'):
                        field = filter.split('=')[0].replace('%20',' ').replace('%2F','/').strip()
                        value = filter.split('=')[1].replace('%20',' ').replace('%2F','/').strip()
                        filter_strings.append('<viz-filter field="{field}" value="{value}"> </viz-filter>'.format(field=field,value=value))
                all_filters = '\n'.join(filter_strings)
                html = '''
                <div class="tableauPlaceholder">
                    <tableau-viz id="tableauViz" src='{tableau_url}' toolbar="bottom" hide-tabs>
                    {all_filters}
                    </tableau-viz>
                </div>
                '''.format(tableau_url=tableau_url,all_filters=all_filters)
                break
        if html:
            return html
        return None


    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot).then(update_dashboard,chatbot,dashboard)
    
    clear.click(None, None, chatbot, queue=False)

    script = '''
    function test(){
        let script = document.createElement('script');
        script.innerHTML = "var viz = new tableau.Viz(containerDiv, document.getElementById('tableauViz').getAttribute('src'), {hideTabs: true});";
        document.head.appendChild(script);  
        }
    '''

    script2 = '''
    function test(){
        let script = document.createElement('script');
        script.type = 'module';
        script.src = 'https://public.tableau.com/javascripts/api/tableau.embedding.3.latest.min.js';
        document.head.appendChild(script);   
        }
    '''

    demo.load(js = script)
    demo.load(js = script2)
    
demo.queue()
# demo.launch()



# print('user:',message_history)

# print("model:",reply_history)
# demo.launch(share=True)
