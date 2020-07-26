from threading import Thread

from flask import Flask, render_template
from tornado.ioloop import IOLoop

from bokeh.embed import server_document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
#from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
import pandas as pd
from bokeh.server.server import Server
from bokeh.themes import Theme

app = Flask(__name__)

class BokehApp(object):
    """
    Start Bokeh App
    """
    
    def __init__(self, file_name=r"../data/nifty50.csv",):
        self.data_sets = self.create_data_sets(file_name)

    def create_data_sets(self, file_name):
        """
        
        """
        main = pd.read_csv(file_name)
        max_by_date = main.groupby(['date']).max().reset_index()
        
        max_by_date['time'] = pd.to_datetime(max_by_date['date'], infer_datetime_format=True)
        max_by_date['temperature'] = max_by_date['close']
        
        # TODO: Remove ColumnDataSource and let bokeh convert internally
        # Looks like callback requires a ColumnDataSource object
        
        return {
                'MAIN': ColumnDataSource(data=main), 
                'MAX_BY_DATE': ColumnDataSource(data=max_by_date)
                }
    
    def add_time_series(self, data_name='MAX_BY_DATE', x_name='time', y_name='temperature'):
        plot = figure(plot_width=888, plot_height=444, x_axis_type='datetime')
        plot.line(x_name, y_name, source=self.data_sets[data_name])
        return plot
    
    def add_slider(self, data_name='MAX_BY_DATE', x_name='time', y_name='temperature'):
        
        def slider_callback(attribute, old_value, new_value):
            print('Callback', attribute, old_value, new_value)
            df = pd.DataFrame(self.data_sets[data_name].data)
            print('DataFrame', df)
            df = df[df[y_name] < new_value]
#            self.data_sets[data_name] = ColumnDataSource(df)
            
        
        df = self.data_sets[data_name].data
        min_value, max_value = df[y_name].min(), df[y_name].max()
        
        slider = Slider(start=min_value, end=max_value, value=0, step=1, title="Slider")
        slider.on_change('value', slider_callback)
        
        return slider
        
    def add_figures(self, document):
        
        time_series = self.add_time_series()
        controls = self.add_slider()
        
        document.add_root(column(controls, time_series))
        document.theme = Theme(filename="theme.yaml")    

@app.route('/', methods=['GET'])
def bkapp_page():
    script = server_document('http://localhost:5006/bkapp')
    return render_template("embed.html", script=script, template="Flask")


def bk_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    bokek_app = BokehApp()
    server = Server({'/bkapp': bokek_app.add_figures}, 
                    io_loop=IOLoop(), 
                    allow_websocket_origin=["localhost:8000"]
                    )
    server.start()
    server.io_loop.start()

Thread(target=bk_worker).start()

if __name__ == '__main__':
    print('Opening single process Flask app with embedded Bokeh application on http://localhost:8000/')
    print()
    print('Multiple connections may block the Bokeh app in this configuration!')
    print('See "flask_gunicorn_embed.py" for one way to run multi-process')
    app.run(port=8000)
