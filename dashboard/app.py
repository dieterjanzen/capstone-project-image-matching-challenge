import os
import base64
import dash
from dash import html,dcc,ctx
from dash.dependencies import Input,Output,State
from dash.exceptions import PreventUpdate
# own .py files
import viz_utilities as vu
import LoFTR_plotly as lp

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]


################################################################################
# APP INITIALIZATION
################################################################################
app = dash.Dash(__name__, external_stylesheets=external_stylesheets,suppress_callback_exceptions=True)
# this is needed by gunicorn command in procfile
server = app.server

################################################################################
# GLOBAL APP VARIABLES
################################################################################

ALLSCENES = ["brandenburg_gate", "british_museum", "buckingham_palace",
 "colosseum_exterior", "grand_place_brussels", "lincoln_memorial_statue",
 "notre_dame_front_facade", "pantheon_exterior", "piazza_san_marco",
 "sacre_coeur", "sagrada_familia", "st_pauls_cathedral", "st_peters_square",
 "taj_mahal", "temple_nara_japan", "trevi_fountain"]
# for tests with a smaller sample size of plots (replotting takes very long):
# ALLSCENES = ["brandenburg_gate", "british_museum"]

INPUT_DIR = '../data/train/' # Has to point to the train directory of the dataset.
PLOT_DIR = "Plots/" # where the directional scatterplots are stored or read from
HOST = os.getenv("HOST", "127.0.0.1") # default for local run: os.getenv("HOST", "127.0.0.1")
PORT = os.getenv("PORT", "8050") # default for local run: os.getenv("PORT", "8050")
DEBUG = False # enables verbose debugging in console and on the dashboard
EMPTYFIGURE = vu.empty_figure() # white placeholder figure

pairings, cal, scalings = vu.load_pairs_and_cal(ALLSCENES,INPUT_DIR)

# default uploadbutton Div Object
uploadbutton = html.Div(
    children=[
        'Drag and Drop or ',
        html.A('Select a File'),
        html.Br(),
        "(allowed formats are .jpg and .png)"
    ],
    style={
        'width': '100%',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'margin': '15px',
        "object-fit":"contain",
        "justify-content":"center"
    }
)
# to display uploaded images in place of the upload button
def imdiv(contents):
    # HTML Img objects accept base64 encoded strings in the same format
    # that is supplied by the upload
    return html.Img(src=contents,style={"height":350,"width":"100%","padding":5, "object-fit":"contain"})


################################################################################
# PLOTS
################################################################################

# This part either reads existing plots from the path provided in PLOT_DIR, or attempts to plot them anew, if it can't find them, afterwards storing them in PLOT_DIR
try: 
    print("attempting to read from existing files")
    figlist = [vu.read_from_json(scene, PLOT_DIR) for scene in ALLSCENES]
    print("Success!")
    figures = dict(zip(ALLSCENES,figlist))
except:
    print("Failure to load from existing files! Would you like to recreate the plots (this may take a few minutes)?")
    recreateflag = input("Type y to proceed: ")
    if recreateflag != ("y" or "Y"):
        raise Exception("Failed to load data.")
    figlist = [vu.plotter(scene, cal, scalings=scalings) for scene in ALLSCENES]
    print("writing new json files")
    figures = dict(zip(ALLSCENES,figlist))
    for scene, figure in zip(ALLSCENES,figlist):
        vu.write_to_json(scene, figure, cal, PLOT_DIR)

################################################################################
# LAYOUT
################################################################################
# MAIN CONTAINER
app.layout = html.Div(
    children=[
        html.H3(children="TWO EYES SEE M👁RE"),  #"◉ 📷 (☉.☉) ◎ 👁 👀"
        html.H6(children="A Capstone-Project by Dr. Dieter Janzen and Dr. Bernd Ackermann"),
        # START TABS
        dcc.Tabs(
            children=[
################################################################################ TAB 1
                dcc.Tab(
                    label="Explore the Google dataset",
                    children=[
                        # VIZ BODY
                        html.Div(
                            style={"height":"50%","width":"98%",'display': 'flex', 'flex-direction': 'row'}, # VIZ BODY CONTAINER STYLE
                            children=[
                                # LEFT HALF CONTAINER
                                html.Div(
                                    style={"width":"40%"}, # % of browser window width
                                    children=[
                                        # UI ELEMENTS
                                        html.Label("Scene"),
                                        dcc.Dropdown(
                                            id="dropdown-menu",
                                            placeholder="Choose a Scene",
                                            options = [{"label": scenetitle.replace("_", " ").title() ,"value": scenetitle} for scenetitle in ALLSCENES]),
                                        html.Label("Threshhold"),
                                        dcc.Slider(
                                            min=0,
                                            max=1,
                                            id="threshhold_slider", 
                                            value=0, 
                                            tooltip={"placement":"bottom","always_visible":True}),
                                        html.Label("Alpha"),
                                        dcc.Slider(
                                            min=0,
                                            max=1,
                                            id="alpha_slider", 
                                            value=0.1, 
                                            tooltip={"placement":"bottom","always_visible":True}),
                                        html.Label("Image scale"),
                                        dcc.Slider(
                                            min=240,
                                            max=1200,
                                            step=40,
                                            id="scale_slider", 
                                            value=840, 
                                            marks={
                                                240:"240 (fast)",
                                                480:"",
                                                720:"",
                                                960:"",
                                                1200:"1200 (slow)"}, 
                                                tooltip={"placement":"bottom","always_visible":True}),
                                        html.Button(
                                            children="reset selection", 
                                            id="resetbutton", 
                                            n_clicks=0),
                                        html.Button(
                                            children="calculate matches", 
                                            id="calculatebutton", 
                                            n_clicks=0),
                                        # INTERACTIVE TOP-DOWN-VIEW PLOT
                                        html.Label(
                                            children="Click two views (arrows) in the plot below", 
                                            style={"text-align":"center","display":"block"}),
                                        dcc.Graph(
                                            id="scatterplot", 
                                            figure = EMPTYFIGURE, 
                                            style={"height":"60%"}),
                                        ]), # END LEFT HALF CONTAINER
                                # RIGHT HALF CONTAINER
                                html.Div(
                                    style = {"width":"60%"}, # % of browser window width 
                                    children=[
                                        # TEXT SELECTION INDICATOR
                                        html.Label(
                                            id="selector", 
                                            children="nothing selected",
                                            style={"font-weight":"bold","text-align":"center","display":"block"}),
                                        # IMAGE SELECTION INDICATOR CONTAINER
                                        html.Div(
                                            style={"height":300,'display': 'flex', 'flex-direction': 'row'},
                                            children=[
                                                html.Img(
                                                    id="implot1", 
                                                    style={"width":"50%","padding":5, "object-fit":"contain"}), # % of right half container width
                                                html.Img(
                                                    id="implot2", 
                                                    style={"width":"50%","padding":5, "object-fit":"contain"})  # % of right half container width
                                                ]), # END IMAGE SELECTION INDICATOR CONTAINER
                                        # LoFTR PAIRING PLOT
                                        html.Img(
                                            id="pairplot", 
                                            style={"width":"100%"}) # % of right half container width
                                        ]) #END RIGHT HALF CONTAINER
                                ]) # END VIZ BODY CONTAINER
                        ]), # END TAB 1
################################################################################ TAB 2
                dcc.Tab(
                    label="Upload custom images",
                    children=[
                        # VIZ BODY
                        html.Div(
                            style={"height":"50%","width":"98%",'display': 'flex', 'flex-direction': 'row'}, # VIZ BODY CONTAINER STYLE
                            children=[
                                # LEFT HALF CONTAINER
                                html.Div(
                                    style = {"width":"40%"}, # % of browser window width
                                    children=[
                                        # UI ELEMENTS
                                        html.Label("Weights"),
                                        dcc.RadioItems(
                                            id="weights_radio", 
                                            options=[{"label":"Outdoors","value":"outdoor"},{"label":"Indoors","value":"indoor"}],
                                            value="outdoor", 
                                            inline=True),
                                        html.Label("Threshhold"),
                                        dcc.Slider(
                                            min=0,
                                            max=1,
                                            id="threshhold_slider_c", 
                                            value=0, 
                                            tooltip={"placement":"bottom","always_visible":True}),
                                        html.Label("Alpha"),
                                        dcc.Slider(
                                            min=0,
                                            max=1,
                                            id="alpha_slider_c", 
                                            value=0.1, 
                                            tooltip={"placement":"bottom","always_visible":True}),
                                        html.Label("Image scale"),
                                        dcc.Slider(
                                            min=240,
                                            max=1200,
                                            step=40,
                                            id="scale_slider_c", 
                                            value=840, 
                                            marks={
                                                240:"240 (fast)",
                                                480:"",
                                                720:"",
                                                960:"",
                                                1200:"1200 (slow)"}, 
                                            tooltip={"placement":"bottom","always_visible":True}),
                                        html.Button(
                                            children="reset selection", 
                                            id="resetbutton_c", 
                                            n_clicks=0),
                                        html.Button(
                                            children="calculate matches", 
                                            id="calculatebutton_c", 
                                            n_clicks=0),
                                        ]), # END LEFT HALF CONTAINER
                                # RIGHT HALF CONTAINER
                                html.Div(
                                    style={"width":"60%"},
                                    children=[
                                        # TEXT SELECTION INDICATOR
                                        html.Label(
                                            id="load_indicator", 
                                            children="Nothing uploaded (don't worry, your images are deleted, as soon as you refresh the page)",
                                            style={"font-weight":"bold","text-align":"center","display":"block"}),
                                        # IMAGE SELECTION INDICATOR CONTAINER
                                        html.Div(
                                            style={"width":"100%",'display': 'flex', 'flex-direction': 'row'},
                                            children=[
                                                dcc.Upload(
                                                    id="imupload1",
                                                    style={"width":"100%","padding":5,"justify-content":"center", "align-items":"center"},
                                                    children=uploadbutton),
                                                dcc.Upload(
                                                    id="imupload2",
                                                    style={"width":"100%","padding":5,"justify-content":"center", "align-items":"center"},
                                                    children=uploadbutton)
                                                ]),
                                        # LoFTR PAIRING PLOT
                                        html.Img(
                                            id="pairplot_c", 
                                            style={"width":"100%"}) # % of right half container width
                                        ]), # END IMAGE SELECTION INDICATOR CONTAINER
                                ]) #END RIGHT HALF CONTAINER
                        ]), # END VIZ BODY CONTAINER
                ]), # END TAB 2
    dcc.Store(
        id="uploadbuffer", 
        data=["",""]),
    dcc.Store(
        id="selectionbuffer", 
        data=[])
    ]) # END APP

################################################################################
# INTERACTION CALLBACKS TAB 1
################################################################################

# dropdown callback for scene selection
@app.callback(
    Output("scatterplot", "figure"),    # Trigger an update of the interactive top-down-view-plot
    Output("resetbutton","n_clicks"),   # Trigger a click on the reset button to remove selections of the prior scene -> causes reset callback in the selector
    Input("dropdown-menu", "value"),    # Callback on change in dropdown-menu value
    State("resetbutton","n_clicks"))    # Read resetbutton state
def update_top_down_graph(scene,reset):
    # 1. takes the current scene and returns the corresponding top-down-plot
    # 2. triggers the reset button to prevent selection errors after switching scenes
    if scene:
        print("plotting scene...")
        fig = figures[scene]
        reset += 1
    else: # not scene means, this callback was triggered during initialization and doesn't need an update
        raise PreventUpdate
    return fig, reset

################################################################################

# selection callback for pair selection and selection reset
@app.callback(
    Output("selector", "children"),     # Update Selector String
    Output("selectionbuffer", "data"),  # Update Selector buffer
    Output("implot1", "src"),           # Display selected image 1
    Output("implot2", "src"),           # Display selected image 1
    Input("scatterplot", "clickData"),  # Callback on clicking a Datapoint in the interactive top-down-view-plot
    Input("resetbutton", "n_clicks"),   # Callback on clicking the reset button to remove current selections
    State("selectionbuffer","data"),    # Check current state of Selector buffer to see the previsously clicked image
    State("dropdown-menu", "value"))    # Check current state of the Scene Selector to gain the scene filepath context
def return_clicked_id(clickData, reset, selections, scene):
    # 1. checks whether the reset button was pressed and consecutively resets the selector, the image plots and the buffer
    # 2. checks whether the clicked point in the topdown plot was already clicked and prevents an update to catch redundancies
    # 3. appends the currently clicked point to the selections, removes the oldest selection to crop selecitons back to two (if necessary)
    # and reads the images for display in the selector
    if scene == None or ctx.triggered_id == None: # prevent update on initial callback trigger
        raise PreventUpdate
    if ctx.triggered_id == "resetbutton" and reset > 0: # did the reset button get triggered?
        print("resetting...")
        return ["nothing selected", [], "",""]
    sel = selections # assign selections from buffer
    clicked = str(clickData["points"][0]["customdata"])+".jpg" # extract image file name from clicked datapoint-id
    if clicked not in sel:
        sel.append(clicked) #append clicked datapoint to current selection list
    else: # clicked the previously selected image. this triggers an Error
        figs = vu.imshow(sel,scene,INPUT_DIR)
        return [f"You can't select the same image twice. You selected {sel[0]} and {sel[1]}", sel, figs[0],figs[1]]
    if len(sel)==1: # clicked first image and starting with an empty selection. return 1 selected image
        figs = vu.imshow(sel,scene,INPUT_DIR)
        return [f"you selected {sel[0]}", sel, figs[0],""]
    elif len(sel)>2: # clicked the third image, overwriting the first selection
        sel = sel[1:3]
    if len(sel)==2: # clicked the second image or selection overwritten to have 2 again. return 2 selected images
        figs = vu.imshow(sel,scene,INPUT_DIR)
        return [f"you selected {sel[0]} and {sel[1]}", sel, figs[0],figs[1]]
    else: # This never triggered, but I'm paranoid about this dashboard
        print("How did you get this selection? - ",sel)
        raise Exception("unexpected selection error")

################################################################################

# Callback to trigger LoFTR Modeling of two selected images and giving out an interconnected pairplot image as result
@app.callback(
    Output("pairplot", "src"),              # plot is output as an image, because dash can't handle matplotlib plots
    Input("calculatebutton", "n_clicks"),   # Trigger Callback on clicking the calculate button
#    Input("resetbutton", "n_clicks"),       # Trigger Callback on clicking the reset button
    State("dropdown-menu", "value"),        # Check currently selected scene for filepath context
    State("selectionbuffer", "data"),       # Check currently selected input images for LoFTR
    State("threshhold_slider", "value"),    # Check currently selected confidence threshhold to filter image matchings
    State("alpha_slider", "value"),         # Check currently selected line alpha to make the connecting lines more/less rtansparent
    State("scale_slider", "value")          # Check currently selected image scale for LoFTR to compute. larger images deliver better results, but take longer to compute
)
def plot_imagepair(calculate, scene, selections,threshhold,alpha,scale):
    # calculates LoFTR image-matchings and visualizes them. plots are buffered as png and base64 encoded to display in an html.Img object.
    if len(selections) != 2 or calculate == 0 or scene == None: # prevent update on initial callback trigger, or if insufficient scenes were selected
        raise PreventUpdate
    print("loading plotpaths")
    imgpath1 = os.path.join(INPUT_DIR,scene,"images",selections[0])
    imgpath2 = os.path.join(INPUT_DIR,scene,"images",selections[1])
    print(imgpath1)
    print(imgpath2)
    print("buffering image")
    buf = lp.single_loftr_figure(imgpath1, imgpath2, alpha = alpha, threshold = threshhold, lines = True, dpi = 150 , res=scale)
    print("encoding")
    imgdata = base64.b64encode(buf.getbuffer()).decode("utf8") # encode to html elements
    print("done")
    return f"data:image/png;base64,{imgdata}"

################################################################################
# INTERACTION CALLBACKS TAB 2
################################################################################

# Upload callback for custom images
@app.callback(
Output("load_indicator", "children"),       # Update Selector String
Output("imupload1","children"),             # Update Upload field 1 (if applicable)
Output("imupload2","children"),             # Update Upload field 2 (if applicable)
Output("uploadbuffer","data"),              # Update the local upload-buffer
Input("imupload1","contents"),              # Trigger when something is loaded into Upload 1
Input("imupload2","contents"),              # Trigger when something is loaded into Upload 2
Input("resetbutton_c","n_clicks"),          # Trigger on Reset
State("imupload1","filename"),              # Read the Upload 1 filename to display in the selector string
State("imupload2","filename"),              # Read the Upload 2 filename to display in the selector string
State("uploadbuffer","data")                # Read to check for previously selected images
)
def upload(contents1=None,contents2=None,reset=0,filename1=None,filename2=None,buffer=["",""]):
    # 1. checks for reset trigger and resets accordingly
    # 2. checks for which upload was the callback trigger, then loads it into the corresponding buffer location
    # 3. updates the buffer and the html.Img objects with the image data and the load indicator string with filenames. 
    if ctx.triggered_id == None: # prevent update on initial callback trigger
        raise PreventUpdate
    elif ctx.triggered_id == "resetbutton_c" and reset > 0: # did the reset button get triggered?
        return "Nothing uploaded",uploadbutton,uploadbutton,["",""]
    elif ctx.triggered_id == "imupload1": # upload 1 triggered?
        buffer[0] = contents1
    elif ctx.triggered_id == "imupload2": # upload 2 triggered?
        buffer[1] = contents2
    loadednames = [filename if img != "" else "" for img,filename in zip(buffer, [filename1,filename2])]
    try:
        loadednames.remove("")
    except ValueError:
        pass
    if len(loadednames)==1:
        loadindicator = f"You uploaded {loadednames[0]}"
    else:
        loadindicator = f"You uploaded {loadednames[0]} and {loadednames[1]}"
    imdivs = [imdiv(img) if img != "" else uploadbutton for img in buffer]
    return loadindicator,imdivs[0],imdivs[1], buffer

################################################################################

# Callback to trigger LoFTR Modeling of two selected images and giving out an interconnected pairplot image as result
@app.callback(
    Output("pairplot_c", "src"),              # plot is output as an image, because dash can't handle matplotlib plots
    Input("calculatebutton_c", "n_clicks"),   # Trigger Callback on clicking the calculate button
    State("uploadbuffer", "data"),       # Check currently selected input images for LoFTR
    State("weights_radio","value"),
    State("threshhold_slider_c", "value"),    # Check currently selected confidence threshhold to filter image matchings
    State("alpha_slider_c", "value"),         # Check currently selected line alpha to make the connecting lines more/less rtansparent
    State("scale_slider_c", "value")          # Check currently selected image scale for LoFTR to compute. larger images deliver better results, but take longer to compute
)
def plot_imagepair_c(calculate, images, weights, threshhold, alpha, scale):
    #modified version of plot_imagepair, capable of handling custom uploaded images
    if len(images) != 2 or calculate == 0: # prevent update on initial callback trigger, or if insufficient scenes were selected
        raise PreventUpdate
    print(f"buffering image")
    buf = lp.single_loftr_figure(images[0], images[1], alpha = alpha, threshold = threshhold, lines = True, dpi = 150 , res=scale, where=weights)
    print("encoding")
    imgdata = base64.b64encode(buf.getbuffer()).decode("utf8") # encode to html elements
    print("done")
    return f"data:image/png;base64,{imgdata}"

################################################################################
# Add the server clause:
# (Change the global variables DEBUG, HOST and PORT at the top of this codepage to avoid breakage)
if __name__ == "__main__":
    app.run(debug=DEBUG, host=HOST,port=PORT)
################################################################################

