library(tidyverse)
library(rvest)
library(janitor)
library(ggplot2)
library(rnaturalearthdata)
library(ggforce)
library(gganimate)
library(sf)
library(gifski)

IBTrACS_Ragasa <- read_html("https://ncics.org/ibtracs/index.php?name=v04r01-2025262N16133#all")

ragasa_table <- IBTrACS_Ragasa %>% 
  html_node(xpath = "//*[@id='content']/table[5]") %>% 
  html_table() %>% 
  clean_names() %>% 
  slice(-1) %>% 
  mutate(across(c(lon, lat, usa_wind, usa_roci),as.numeric)) %>% 
  mutate(date_time = seq(from = as.POSIXct("2025-09-18 12:00:00", tz = "UTC"),
                         to = as.POSIXct("2025-09-23 00:00:00", tz = "UTC"),
                         by = "3 hours"))

ragasa_sf <- st_as_sf(ragasa_table, coords = c("lon", "lat"), crs = 4326)

ragasa_circles <- ragasa_sf %>%
  mutate(geometry = st_buffer(geometry, dist = usa_roci * 1852)) %>%  # divide by 60 convert nautical miles to degrees
  st_transform(4326) %>% 
  mutate(frame = row_number())
  
asia_map <- ne_countries(10, continent = c("Asia"))

gg_asia <- ggplot(asia_map) + 
  geom_sf(aes(fill = name)) +
  coord_sf(xlim = c(100, 140), ylim = c(10, 30)) 

affected_countries <- st_intersection(asia_map, ragasa_circles) %>% 
  mutate(frame = frame)

ragasa_path <- gg_asia + 
  geom_circle(data = ragasa_table %>% mutate(frame = row_number()), 
              aes(x0 = lon, y0 = lat, r = usa_roci/60), 
              color = NA, fill = "red",
              alpha = .1) +
  geom_point(data = ragasa_table %>% mutate(frame = row_number()),
             aes(x = lon, y = lat, size = usa_wind)) +
  geom_label(
    data = affected_countries,
    aes(label = name, geometry = geometry),
    stat = "sf_coordinates",
    color = "black", size = 6, fill = "white"
  ) +
  theme_minimal() +
  theme(legend.position = "none",
        axis.text.y = element_blank(), 
        axis.ticks.y = element_blank(), 
        axis.title.y = element_blank(),
        axis.line.y = element_blank(),
        axis.text.x = element_blank(), 
        axis.ticks.x = element_blank(), 
        axis.title.x = element_blank(),
        axis.line.x = element_blank(),
        plot.title = element_text(size = 20, face = "bold", color = "black")) +
  transition_manual(frames = frame) +
  labs(
    title = "Typhoon Ragasa - Date: {format(ragasa_circles$date_time[frame], '%Y-%m-%d %H:%M')}"
  )

animate(ragasa_path, nframes = max(ragasa_circles$frame), 
        fps = 5, width = 1920, height = 1080, renderer = gifski_renderer())



  
  

