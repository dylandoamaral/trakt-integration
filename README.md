<h1 align="center">Trakt Integration</h1>

<p align="center">
  <a href="https://github.com/custom-components/hacs">
    <img src="https://img.shields.io/badge/HACS-Default-orange.svg" alt="HACS" />
  </a>
  <a href="https://github.com/dylandoamaral/trakt-integration">
    <img src="https://img.shields.io/github/v/release/dylandoamaral/trakt-integration" alt="Release" />
  </a>
  <a href="https://github.com/dylandoamaral/trakt-integration">
    <img src="https://img.shields.io/github/last-commit/dylandoamaral/trakt-integration" alt="Last Commit" />
  </a>
  <a href="https://www.buymeacoffee.com/dylandoamaral">
    <img src="https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow" alt="Donate Coffee" />
  </a>
</p>

<p align="center">
  View your Trakt calendar items in <a href="https://github.com/custom-cards/upcoming-media-card">Upcoming Media Card</a> on a Home Assistant dashboard.
</p>

<p align="center">
  :warning: This is still an early release. It may not be stable and it may have bugs. :warning:<br />
  See the <a href="https://github.com/dylandoamaral/trakt-integration/issues">Issues</a> page to report a bug or to add a feature request.
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/dylandoamaral/trakt-integration/main/images/showcase.png" alt="Showcase Example" />
</p>

<p align="center">
  The image above was generated using <a href="https://github.com/custom-cards/upcoming-media-card">Upcoming Media Card</a> and <a href="https://github.com/dylandoamaral/upcoming-media-card-modification">Upcoming Media Card modification</a>.
</p>

---

## Recommendations 💡

Having the following installed in Home Assistant will help best use this integration:

- [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card)

## Installation 🏠

Installation is a multi-step process. Follow each of the following steps.

### 1. Add HACS Integration

This integration is available in [HACS](https://hacs.xyz/) (Home Assistant Community Store). Install it as follows:

- In Home Assistant, go to HACS > Integrations
- Press the **Explore & Add Repositories** button
- Search for "Trakt"
  - Note: There are two Trakt integrations.
    Choose the one with the description "A Trakt integration for Home Assistant compatible with upcoming media card".
    See [Why not use sensor.trakt?](#why-not-use-sensortrakt-)
- Press the **Install this repository in HACS** button
- Press the **Install** button

### 2. Update Configuration File

The following shows all of the integration's default settings.
Add it as a top-level key (i.e., `trakt_tv:` is not indented) in the `configuration.yaml` file:

```yaml
trakt_tv:
  language: en # Preferred language for movie/show title
  timezone: Europe/Paris # Preferred timezone
  sensors:
    upcoming:
      show:
        days_to_fetch: 90 # How many days in the future you want to fetch
        max_medias: 3 # How many medias you want to fetch
      new_show:
        days_to_fetch: 90
        max_medias: 3
      premiere:
        days_to_fetch: 90
        max_medias: 3
      movie:
        days_to_fetch: 90
        max_medias: 3
      dvd:
        days_to_fetch: 90
        max_medias: 3
    next_to_watch:
      all:
        max_medias: 5
        exclude:
          - veep
          - the-original
          - friends
      only_aired:
        max_medias: 5
        exclude:
          - veep
          - the-original
          - friends
      only_upcoming:
        max_medias: 5
```

#### Integration Settings

- `language` should be an [ISO 639-1 codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) (default is "en")
- `timezone` should be a [pytz timezone](https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568) (default is the server timezone)

#### Available Sensors

By default, this integration does not create any sensors.
The settings that you include in the `configuration.yaml` file determines which sensors are created.
This keeps you from having useless sensors that you don't need, such as the DVD sensor which will likely not fetch anything from the Trakt API,
but you can still use it if you want to.

##### Upcoming sensors

Upcoming sensors are sensors giving the next anticipated movies or shows from your watch list.

There are five sensors available under the `sensors` > `upcoming` array:

- `show` for [TV Shows](https://trakt.tv/calendars/my/shows/) (actually, episodes). Creates `sensor.trakt_upcoming_shows`
- `new_show` for [New Shows](https://trakt.tv/calendars/my/new-shows/) (series premiers). Creates `sensor.trakt_upcoming_new_shows`
- `premiere` for [Season Premieres](https://trakt.tv/calendars/my/premieres/). Creates `sensor.trakt_upcoming_premieres`
- `movie` for [Movies](https://trakt.tv/calendars/my/movies/) premieres. Creates `sensor.trakt_upcoming_movies`
- `dvd` for [DVD & Blu-ray](https://trakt.tv/calendars/my/dvd/) releases. Creates `sensor.trakt_upcoming_dvds`

There are two parameters for each sensor:

- `days_to_fetch` should be a positive number for how many days to search
- `max_medias` should be a positive number for how many items to grab

##### All Upcoming sensors

All Upcoming sensors are sensors giving the next anticipated movies or shows.

There are five sensors available under the `sensors` > `all_upcoming` array:

- `show` for [TV Shows](https://trakt.tv/calendars/shows/) (actually, episodes). Creates `sensor.trakt_all_upcoming_shows`
- `new_show` for [New Shows](https://trakt.tv/calendars/new-shows/) (series premiers). Creates `sensor.trakt_all_upcoming_new_shows`
- `premiere` for [Season Premieres](https://trakt.tv/calendars/premieres/). Creates `sensor.trakt_all_upcoming_premieres`
- `movie` for [Movies](https://trakt.tv/calendars/movies/) premieres. Creates `sensor.trakt_all_upcoming_movies`
- `dvd` for [DVD & Blu-ray](https://trakt.tv/calendars/dvd/) releases. Creates `sensor.trakt_all_upcoming_dvds`

There are two parameters for each sensor:

- `days_to_fetch` should be a positive number for how many days to search
- `max_medias` should be a positive number for how many items to grab

##### Recommendation sensors

Recommendation sensors are sensors giving media that you may like.

There are five sensors available under the `sensors` > `recommendation` array:

- `show` for TV Shows. Creates `sensor.trakt_recommendation_shows`
- `movie` for Movies. Creates `sensor.trakt_recommendation_movies`

There are one parameter for each sensor:

- `max_medias` should be a positive number for how many items to grab

##### Next To Watch sensor

Next To Watch sensor is sensor giving the next show to watch depending on your progress.

There only one sensor available under the `sensors` > `next_to_watch` array:

- `all` for all TV Shows progress. Creates `sensor.trakt_next_to_watch_all`
- `only_aired` for only aired TV Shows progress. Creates `sensor.trakt_next_to_watch_only_aired`
- `only_upcoming` for only upcoming TV Shows progress. Creates `sensor.trakt_next_to_watch_only_upcoming`

There are three parameters for each sensor:

- `max_medias` should be a positive number for how many items to grab
- `exclude` should be a list of shows you'd like to exclude, since it's based on your watched history. To find keys to put there, go on trakt.tv, search for a show, click on it, notice the url slug, copy/paste it. So, if I want to hide "Friends", I'll do the steps mentioned above, then land on https://trakt.tv/shows/friends, I'll just have to copy/paste the last part, `friends`, that's it
  You can also use the Trakt.tv "hidden" function to hide a show from [your calendar](https://trakt.tv/calendars/my/shows) or the [progress page](https://trakt.tv/users/<username>/progress)
- `sort_by` _OPTIONAL_ should be a string for how to sort the list. Default is `released`. Possible values are:
  - `released`, `title`, `trakt`
- `sort_order` _OPTIONAL_ should be a string for the sort order. Possible values are `asc`, `desc`. Default is `asc`

##### Anticipated Sensors

- `sensor.trakt_anticipated_shows`: This sensor displays the most anticipated TV shows on Trakt.
- `sensor.trakt_anticipated_movies`: This sensor displays the most anticipated movies on Trakt.

### Example Configuration

To enable these sensors, you can use the following configuration:

```yaml
trakt_tv:
  language: en
  timezone: America/Los_Angeles
  sensors:
    anticipated:
      movie:
        max_medias: 10
      show:
        max_medias: 10
```

You can also exclude collected items from these sensors:

```yaml
trakt_tv:
  language: en
  timezone: America/Los_Angeles
  sensors:
    anticipated:
      movie:
        exclude_collected: true
        max_medias: 10
      show:
        exclude_collected: true
        max_medias: 10
```

##### Watchlist Movies Sensor

This sensor displays movies from your personal Trakt.tv watchlist. It's highly configurable to help you decide what to watch next.

- `sensor.trakt_watchlist_movies`: Creates a sensor with movies from your watchlist.

###### Configuration

```yaml
trakt_tv:
  sensors:
    watchlist:
      movie:
        # Only include movies that have already been released.
        # Default: true
        only_released: true
        # Exclude movies that you have already marked as watched or
        # added to your collection on Trakt.
        # Default: true
        only_unwatched: true
        # The maximum number of movies to show.
        # Default: 20
        max_medias: 20
        # How to sort the list of movies.
        # Options: "released", "title", "added", "rating"
        # Default: "released"
        sort_by: released
        # The sort order.
        # Options: "asc", "desc"
        # Default: "asc"
        sort_order: asc
```

##### Lists sensor

Lists sensor allows you to fetch both public and private lists from Trakt, each list will be a sensor. The items in the list will be sorted by their rank on Trakt.

There are four parameters for each sensor:

- `friendly_name` **MANDATORY** should be a string for the name of the sensor. This has to be unique for each list.
- `list_id` **MANDATORY** should be the Trakt list ID. For public lists the ID has to be numeric, for private lists the ID can be either the numeric ID or the slug from the URL. To get the numeric ID of a public list, copy the link address of the list before opening it or open the Report List window. This will give you a URL like `https://trakt.tv/lists/2142753`. The `2142753` part is the numeric ID you need to use
- `private_list` _OPTIONAL_ has to be set to `true` if using your own private list. Default is `false`
- `media_type` _OPTIONAL_ can be used to filter the media type within the list, possible values are `show`, `movie`, `episode`. Default is blank, which will show all media types
- `max_medias` _OPTIONAL_ should be a positive number for how many items to grab. Default is `3`
- `sort_by` _OPTIONAL_ should be a string for how to sort the list. Default is `rank`. Possible values are:
  - `rank`, `added`, `title`, `released`, `runtime`, `popularity`, `random`, `percentage`, `my_rating`, `watched`, `collected`, `trakt`
  - Some options are VIP only: `imdb_rating`, `tmdb_rating`, `rt_tomatometer`, `rt_audience`, `metascore`, `votes`, `imdb_votes`, and `tmdb_votes`. The results will default to `rank` if not a VIP user
- `sort_order` _OPTIONAL_ should be a string for the sort order. Possible values are `asc`, `desc`. Default is `asc`

###### Lists Example

```yaml
trakt_tv:
  sensors:
    lists:
      - friendly_name: "Favorites"
        private_list: True # Set to True if the list is your own private list
        list_id: "favorites" # Can be the slug, because it's a private list
        max_medias: 5
      - friendly_name: "2024 Academy Awards"
        list_id: 26885014
        max_medias: 5
        sort_by: rating_trakt # Sort by Trakt user rating instead of list rank
        sort_order: desc
      - friendly_name: "Star Trek Movies"
        list_id: 967660
        media_type: "movie" # Filters the list to only show movies
        max_medias: 5
```

##### Stats sensors

Creates individual sensors giving all of your stats about the movies, shows, and episodes you have watched, collected, and rated.
Add `sensors` > `stats` with a list of the sensors you want to enable. You can enable all of them instead by adding `all` to the list.

The available stats are available:

- `movies_plays`
- `movies_watched`
- `movies_minutes`
- `movies_collected`
- `movies_ratings`
- `movies_comments`
- `shows_watched`
- `shows_collected`
- `shows_ratings`
- `shows_comments`
- `seasons_ratings`
- `seasons_comments`
- `episodes_plays`
- `episodes_watched`
- `episodes_minutes`
- `episodes_collected`
- `episodes_ratings`
- `episodes_comments`
- `network_friends`
- `network_followers`
- `network_following`
- `ratings_total`

###### Stats Example

```yaml
trakt_tv:
  sensors:
    # Create sensors for all available stats
    stats:
      - all

    # OR

    # Create sensors for specific stats (see available stats above)
    stats:
      - episodes_plays
      - movies_minutes
```

#### Configuration Example

For example, adding only the following to `configuration.yaml` will create two sensors.
One with the next 10 TV episodes in the next 30 days and another with the next 5 movies coming out in the next 45 days:

```yaml
trakt_tv:
  language: en
  sensors:
    upcoming:
      show:
        days_to_fetch: 30
        max_medias: 10
      movie:
        days_to_fetch: 45
        max_medias: 5
    recommendation:
      show:
        max_medias: 3
      movie:
        max_medias: 3
```

### 3. Restart Home Assistant

- Confirm the `configuration.yaml` is valid in Configuration > Server Controls > Configuration validation > **Check Configuration** button
- Restart your Home Assistant server in Configuration > Server Controls > Server management > **Restart** button

Note: You will not see anything new in Home Assistant yet.

### 4. Prepare Trakt

You have to provide a `client_id` and a `client_secret` to use this integration. Get these keys with the following:

- Go to the [Trakt API Apps](https://trakt.tv/oauth/applications) page and press the **New application** button
- Fill in the **Name** (required) and **Description** (optional) fields. These fields are just for your own reference
- Fill in **Redirect uri** with one of the following
  - Default: `https://my.home-assistant.io/redirect/oauth`
  - If you have disabled [My Home Assistant](<[url](https://www.home-assistant.io/integrations/my)>) on your installation
    - If you use HA Cloud: `https://<ha-cloud-remote-url>/auth/external/callback`
    - If you do not use HA Cloud: `https://<your-ha-server-address>:<port>/auth/external/callback`
- Do not enter anything in **Javascript (cors) origins** and do not select any **Permissions**
- Press the **Save app** button
- Record the displayed `client_id` and `client_secret`
  - Note: You do not need to press the **Authorize** button!

### 5. Add Home Assistant Integration

- In Home Assistant, go to Configuration > Integrations
- Press the **Add Integration** button
- Search for "Trakt" and click on it
- Enter the `client_id` and `client_secret` from Trakt
- Press the **Submit** button
- Press the **Finish** button

Depending on the options you set in the `configuration.yaml` file, the sensors may take a while to be created and populated.

### 6. Add an Upcoming Media Card

Go to your Dashboard, enable editing, and add a manual card like the following:

```yaml
type: custom:upcoming-media-card
entity: sensor.trakt_upcoming_shows
title: Upcoming Episodes
image_style: fanart
hide_empty: true
title_text: $title
line1_text: $episode
line2_text: $number
line3_text: $day, $date $time
line4_text: $empty
max: 10
```

See the [Upcoming Media Card](https://github.com/custom-cards/upcoming-media-card) page for formatting and display options to add to your card.

---

## Workaround

Some people are unable to use the integration because the OAUTH authentification is not working.

Thanks @blizzrdof77 and @robloh for the following workaround:

1. go to https://my.home-assistant.io/ and enter the correct path to my instance (example: http://172.30.1.11:8123/)
2. instead of entering your local address (http://172.30.1.11:8123/) in the TRAKT application page, enter this: https://my.home-assistant.io/redirect/oauth
3. add the integration
4. accept in TRAKT
5. then accept in the my home assistant page that showed up
6. profit

## Additional Information ℹ️

### Why not use sensor.trakt ?

There is already another integration for Trakt, [sensor.trakt](https://github.com/custom-components/sensor.trakt). However, I decided to create my own integration for the following reasons:

- The other integration is almost never updated
- They haven't accepted my [pull request](https://github.com/custom-components/sensor.trakt/pull/58) for more than 3 months, so I modified it in my local environment to meet my needs
- This integration provides more features than the old one
  - Fetch more than 33 days (the single-query limitation on Trakt)
  - Have both the Movies and TV Shows calendars at the same time
  - Use other Trakt calendars such as Premieres, New Shows, and DVD & Blu-ray releases

### Feature Requests and Contributions

Don't hesitate to [ask for features](https://github.com/dylandoamaral/trakt-integration/issues) or contribute your own [pull request](https://github.com/dylandoamaral/trakt-integration/pulls). ⭐

### For Developers

If you want to add a feature or fix a bug by yourself, follow these instructions:

1. Use [Visual Studio Code](https://github.com/microsoft/vscode) and use [dev containers](https://github.com/microsoft/vscode-dev-containers)
2. In a browser open `localhost:8123`
3. Add the trakt integration
4. Start to develop a new feature

:info: To restart home assistant use `make homeassistant`
