# Tasking manager stats
> Various stats and visualizations computed from HOT tasking manager data to promote missing maps activity

## Map evolution

The visualization proposes to see again the map of the tasking manager day by day.

Technically it generates a directory of images which can be used to do a video.
Example of this image generation: 

![Map evolution example](Map_evolution.png)


### Basic Installation

#### Windows

- [Download the archive](https://drive.google.com/open?id=1EKbJn4NxjA8fYNR-NTT-KpiaSSJNiU0L)
- Extract the archive

#### Linux/Mac

Coming soon

### Contributor Installation

If you want contribute to the project or 

[Install conda](https://docs.conda.io/en/latest/miniconda.html)

Create a conda environment
````
conda create -n tasking_manager_stats python=3.6
````

Activate the conda environment
````
activate tasking_manager_stats
````

Install the packages with the following command
````
conda install pillow tqdm pandas matplotlib numpy requests
````

#### Optionnal

If you want release your development, you can use the Pyinstaller package.

There is currently an issue in the latest release of Pyinstaller
which is fixed in the develop branch. To install it, run the following command.

````
pip install https://github.com/pyinstaller/pyinstaller/tarball/develop 
````

To release, run the following command
````
pyinstaller tasking_manager_stats/generate_map_evolution.py -F
````


### Usage
#### Windows

* Open *generate_map_evolution.bat* with a text editor.
* Replace *5504* by the id of the tasking manager project
* Replace *data/Mapathons.csv* by the path of the CSV file
or remove *-ev data/Mapathons.csv* if you don't want event
* Save your edit
* Double click on *generate_map_evolution.bat*

If there was no issue, you will have something like this.

![Map evolution result](Map_evolution_result.png)

In the directory *data/<project_id>* you will find all the images.

You can find a tutorial on [how using these images to do a video in the wiki](https://github.com/NicolasGrosjean/tasking_manager_stats/wiki/How-to-create-a-video-with-the-generated-images).

#### Linux/Mac

Coming soon

#### Contributor

Run the following command to know the parameters.

````
python tasking_manager_stats/generate_map_evolution.py -h
````


## License

Tasking manager stats is released under the [MIT License](http://www.opensource.org/licenses/MIT).
