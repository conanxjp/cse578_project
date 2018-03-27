require('jsonlite')
require('plyr')
require('rgdal')
setwd(dirname(parent.frame(2)$ofile))
stateData <- fromJSON('./map_data/us_cities.json')
center <- fromJSON('./map_data/cities.json')
#polygon <- fromJSON("../test/cities.lfs.geojson")

properties <-stateData$features$properties
geometries <- stateData$features$geometry
types <- stateData$features$type
center$stateAbb <- state.abb[match(center$state, state.name)]
center$stateAbb[is.na(center$stateAbb)] <- 'DC'
#polygon_properties <- polygon$features$properties
#polygon_geometry <- polygon$features$geometry

data <- merge(center, properties,  by.x = c('city', 'stateAbb'), by.y = c('AREANAME', 'ST'), sort = T)

index <- c()
for (i in 1:nrow(data)) {
  temp <- which(polygon_properties$NAME == data[i,]$city & polygon_properties$STATEFP == data[i,]$STFIPS)
  index <- c(index, temp)
}
data <- merge(data, polygon_properties[,c('NAME','STATEFP')], by.x = c('city', 'STFIPS'), by.y = c('NAME', 'STATEFP'))
data$type <- polygon_geometry[index,]$type
data$coordinates <- polygon_geometry[index,]$coordinates
data$rank <- as.numeric(data$rank)
data <- data[order(data$rank,data$city),]
geometry <- data[,c('type', 'coordinates')]
drops <- c('state', 'CLASS', 'STFIPS', 'PLACEFIP', 'type', 'coordinates')
data <- data[,!(names(data) %in% drops)]

stateData$features <- stateData$features[1:979,]
stateData$features$properties <- data
stateData$features$geometry <- geometry
output <- toJSON(stateData, pretty = T, auto_unbox = T)
write(output, 'output.json')

