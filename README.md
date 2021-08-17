<h1 align="center">Trakt Integration</h1>

<p align="center">
  <a href="https://github.com/custom-components/hacs">
    <img src="https://img.shields.io/badge/HACS-Default-orange.svg" />
  </a>
  <a href="https://github.com/dylandoamaral/trakt-integration">
    <img src="https://img.shields.io/github/v/release/dylandoamaral/trakt-integration" />
  </a>
  <a href="https://github.com/dylandoamaral/trakt-integration">
    <img src="https://img.shields.io/github/commit-activity/m/dylandoamaral/trakt-integration" />
  </a>
  <a href="https://www.buymeacoffee.com/dylandoamaral">
    <img src="https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow" />
  </a>
</p>

<p align="center">An integration of Trakt calendar that works well with <a href="https://github.com/custom-cards/upcoming-media-card">upcoming media card</a>.</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/dylandoamaral/trakt-integration/main/images/showcase.png" />
</p>

## Install 🏠

:warning: Versions 0.x.x are not very stable and still have many bugs. Please create an issue if you encounter a bug or have a feature request.

### HACS (recommended)

This integration is available in [HACS](https://hacs.xyz/) (Home Assistant Community Store).

When installed you have to provide a `client_id` and a `client_secret`. Here are the steps to get this identifier:
- Create a new application at `https://trakt.tv/oauth/applications`
- Use the following redirect_uri:
  - With HA cloud configured: `https://<cloud-remote-url>/auth/external/callback`
  - Without HA cloud configured: `http://<local-ip>:/auth/external/callback`
- Save the application and then note down the `client_id` and `client_secret`

When this is done, the integration will not generate sensors immediately. You also have to provide the trakt configuration to specify which sensors you want. **[More info](https://github.com/dylandoamaral/trakt-integration#upcoming-media-card)**

## Configuration ⚙️

Trakt integration is highly customizable.

Put the following configuration in your `configuration.yaml`:

```yaml
trakt_tv:
  language: en # Prefered language for movie/show title
  update_interval: 30 # API fetching in minutes
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
```

Everything in the configuration is optional and has a default value (all the values above are the default values for each field).

### Global value

- `language` should be an [ISO 639-1 codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes).
- `update_interval` should be a positive number in minutes

### Upcoming media card

Every upcoming media card sensor is located in `sensors` -> `upcoming`.
By default, the integration does not create any sensors. You have to specify them inside your configuration to create them. It allows you not to create useless sensors that you will not use such as the sensor related to the `DVDs` and fetch the trakt API for nothing.

For example, the following configuration will create two sensors. One that lists your shows and another one that list your movies:

```yaml
trakt_tv:
  language: en
  update_interval: 30
  sensors:
    upcoming:
      show:
        days_to_fetch: 30
        max_medias: 5
      new_show:
        days_to_fetch: 90
        max_medias: 3
```

There are two parameters for each sensor:

- `days_to_fetch` should be a positive number
- `max_medias` should be a positive number

## Additional information ℹ️

### Why not use sensor.trakt ?

There is already another integration for trakt ([sensor.trakt](https://github.com/custom-components/sensor.trakt)). However I still decided to create my own integration for the following reasons:
- The other integration is almost never updated.
- They didn't accept my pull request in 3 months (https://github.com/custom-components/sensor.trakt/pull/58) so I had to modify the integration in my local environment to fullfill my need.
- This integration provides more features than the old one such as the possibility to fetch more than 33 days (trakt single query limitation), the possibility to have both the movies and shows calendars at the same time, the possibility to have the movie calendar and other available calendars such as premiere or dvd.
- This integration doesn't depends to any other library (even if I would like to use pydantic so much ARGHHH).

### Contribution

Don't hesitate to ask for features or to contribute by yourself ⭐.

## For developers 👨‍💻

If you want to add a feature or fix a bug by yourself, follow these instructions:

1. Use [Visual Studio Code](https://github.com/microsoft/vscode) and use [dev containers](https://github.com/microsoft/vscode-dev-containers)
2. Run the `Run Home Assistant on port 9123`.
3. Add the trakt integration.
4. Start to develop a new feature.
