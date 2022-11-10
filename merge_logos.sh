#!/bin/bash

convert fmi-logo.png tropomi-logo.png -resize x80 -background white -splice 20x0+0+0  +append -chop 20x0+0+0 logos.png
