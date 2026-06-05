#!/usr/bin/env python3
"""
Download trending movies from IMDb using GraphQL API
"""
import os
import requests
import json
import time
import argparse
import re


BASE_URL = "https://caching.graphql.imdb.com/"
OPERATION_NAME = "Trending"

HEADERS = {
    'accept': 'application/graphql+json, application/json',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
    'origin': 'https://www.imdb.com',
    'priority': 'u=1, i',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'
}

class ImdbClient:

  def __init__(self): 
      pass  

  def get_trending_movies(self, count=25, data_window="HOURS"):
      """Fetch trending movies from IMDb"""
      payload = {
          'query': """query Trending($first: Int!, $input: TopTrendingInput!) {
            topTrendingTitles(first: $first, input: $input) {
              edges {
                node {
                  item {
                    id
                    titleText {
                      text
                    }
                    originalTitleText {
                      text
                    }
                    titleType {
                      text
                    }
                    releaseYear {
                      year
                    }
                    releaseDate {
                      day
                      month
                      year
                    }
                    runtime {
                      seconds
                    }
                    ratingsSummary {
                      aggregateRating
                      voteCount
                    }
                    genres {
                      genres {
                        text
                      }
                    }
                    certificate {
                      rating
                      country {
                        text
                      }
                    }
                    spokenLanguages {
                      spokenLanguages {
                        text
                        id
                      }
                    }
                    plot {
                      plotText {
                        plainText
                      }
                    }
                    primaryImage {
                      url
                      width
                      height
                    }
                    principalCredits {
                      category {
                        text
                      }
                      credits {
                        name {
                          id
                          nameText {
                            text
                          }
                        }
                        ... on Cast {
                          characters {
                            name
                          }
                        }
                      }
                    }

                  }
                  rank
                }
              }
            }
          }""",
          'operationName': OPERATION_NAME,
          'variables': {
              "first": count,
              "input": {
                  "dataWindow": data_window,
                  "trafficSource": "XWW"
              }
          }
      }
      
      response = requests.post(BASE_URL, headers=HEADERS, json=payload)
      if response.status_code != 200:
        print(f"Response: {response.text}")
        response.raise_for_status()
      return response.json()

  def extract_movie_info(self, data):
      """Extract movie details from trending response"""
      movies = []
      edges = data.get("data", {}).get("topTrendingTitles", {}).get("edges", [])
      
      for edge in edges:
          node = edge.get("node", {})
          item = node.get("item", {})
          
          # Basic info
          movie_id = item.get("id")
          title = (item.get("titleText") or {}).get("text")
          original_title = (item.get("originalTitleText") or {}).get("text")
          title_type = (item.get("titleType") or {}).get("text")
          release_year = (item.get("releaseYear") or {}).get("year")
          
          # Release date
          release_date = item.get("releaseDate")
          full_release_date = None
          if release_date and isinstance(release_date, dict):
              day = release_date.get("day")
              month = release_date.get("month")
              year = release_date.get("year")
              if year:
                  full_release_date = f"{year}-{month or '01'}-{day or '01'}"
          
          # Runtime
          runtime_data = item.get("runtime")
          runtime_seconds = runtime_data.get("seconds") if runtime_data else None
          runtime_minutes = runtime_seconds // 60 if runtime_seconds else None
          
          # Ratings
          ratings = item.get("ratingsSummary")
          rating = ratings.get("aggregateRating") if ratings else None
          vote_count = ratings.get("voteCount") if ratings else None
          
          # Genres
          genres = []
          genre_data = item.get("genres", {})
          if genre_data:
              for genre in genre_data.get("genres", []):
                  if genre and genre.get("text"):
                      genres.append(genre.get("text"))
          
          # Plot
          plot_data = item.get("plot", {})
          plot = plot_data.get("plotText", {}).get("plainText") if plot_data else None
          
          # Image
          primary_image = (item.get("primaryImage") or {})
          poster_url = primary_image.get("url")
          image_width = primary_image.get("width")
          image_height = primary_image.get("height")
          
          # Credits (cast, directors, writers)
          credits_by_category = {}
          principal_credits = item.get("principalCredits", [])
          for credit_group in principal_credits:
              category = credit_group.get("category", {}).get("text", "Unknown")
              credits = credit_group.get("credits", [])
              
              category_credits = []
              for credit in credits:
                  name_info = credit.get("name", {})
                  name = name_info.get("nameText", {}).get("text")
                  name_id = name_info.get("id")
                  
                  # Character info for cast
                  characters = [] 
                  for char in credit.get("characters") or []:
                      if char:
                          characters.append(char.get("name"))
                  
                  if name:
                      credit_info = {
                          "name": name,
                          "id": name_id
                      }
                      if characters:
                          credit_info["characters"] = characters
                      category_credits.append(credit_info)
              
              if category_credits:
                  credits_by_category[category] = category_credits
          
          # Keywords - removed due to API limitations
          keywords = []
          
          if movie_id:
              movies.append({
                  "id": movie_id,
                  "title": title,
                  "original_title": original_title,
                  "title_type": title_type,
                  "release_year": release_year,
                  "release_date": full_release_date,
                  "runtime_minutes": runtime_minutes,
                  "rating": rating,
                  "vote_count": vote_count,
                  "genres": genres,
                  "plot": plot,
                  "poster_url": poster_url,
                  "image_dimensions": {"width": image_width, "height": image_height} if image_width and image_height else None,
                  "credits": credits_by_category,
                  "keywords": keywords,
                  "rank": node.get("rank")
              })
      
      return movies

  def get_movie_details(self, movie_id):
      """Get detailed movie information by IMDb ID"""
      payload = {
          'query': """query GetTitle($id: ID!) {
            title(id: $id) {
                id
                titleText {
                  text
                }
                originalTitleText {
                  text
                }
                titleType {
                  text
                  id
                }
                releaseYear {
                  year
                }
                releaseDate {
                  day
                  month
                  year
                }
                runtime {
                  seconds
                }
                ratingsSummary {
                  aggregateRating
                  voteCount
                }
                metacritic {
                  metascore {
                    score
                  }
                }
                genres {
                  genres {
                    text
                    id
                  }
                }
                plot {
                  plotText {
                    plainText
                  }
                  language {
                    id
                  }
                }
                primaryImage {
                  url
                  width
                  height
                  caption {
                    plainText
                  }
                }
                imageCount: images {
                  total
                }
                videoCount: videos {
                  total
                }
                principalCredits {
                  category {
                    text
                    id
                  }
                  credits {
                    name {
                      id
                      nameText {
                        text
                      }
                      primaryImage {
                        url
                      }
                    }
                    ... on Cast {
                      characters {
                        name
                      }
                    }
                    attributes {
                      text
                    }
                  }
                }
                certificate {
                  rating
                  country {
                    text
                  }
                }
                spokenLanguages {
                  spokenLanguages {
                    text
                    id
                  }
                }
                countriesOfOrigin {
                  countries {
                    text
                    id
                  }
                }
                productionStatus {
                  currentProductionStage {
                    text
                    id
                  }
                }
                canHaveEpisodes
                series {
                  series {
                    id
                    titleText {
                      text
                    }
                    releaseYear {
                      year
                    }
                  }
                }
                episodes {
                  episodes {
                    total
                  }
                }
                titleGenres {
                  genres {
                    genre {
                      text
                    }
                  }
                }
                companyCredits {
                  edges {
                    node {
                      company {
                        id
                        companyText {
                          text
                        }
                      }
                      category {
                        text
                      }
                    }
                  }
                }
                technicalSpecifications {
                  soundMixes {
                    items {
                      text
                    }
                  }
                  aspectRatios {
                    items {
                      aspectRatio
                    }
                  }
                  colorations {
                    items {
                      text
                    }
                  }
                }



                akas {
                  edges {
                    node {
                      text
                      country {
                        text
                      }
                    }
                  }
                }
                meterRanking {
                  currentRank
                  rankChange {
                    changeDirection
                    difference
                  }
                }
                keywords {
                  edges {
                    node {
                      text
                    }
                  }
                }
                latestTrailer {
                  id
                  name {
                    value
                  }
                  thumbnail {
                    url
                  }
                  runtime {
                    value
                  }
                  playbackURLs {
                    displayName {
                      value
                    }
                    url
                  }
                  contentType {
                    displayName {
                      value
                    }
                  }
                  createdDate
                }
                reviews(first: 1) {
                  total
                }
                connections {
                  edges {
                    node {
                      associatedTitle {
                        id
                        titleText {
                          text
                        }
                        releaseYear {
                          year
                        }
                      }
                      category {
                        text
                      }
                    }
                  }
                }
                moreLikeThisTitles(first: 5) {
                  edges {
                    node {
                      id
                      titleText {
                        text
                      }
                      releaseYear {
                        year
                      }
                      ratingsSummary {
                        aggregateRating
                      }
                      primaryImage {
                        url
                      }
                    }
                  }
                }
                titleGenres {
                  genres {
                    genre {
                      text
                    }
                  }
                }
                canRate {
                  isRatable
                }
                isAdult
                titleGenres {
                  genres {
                    genre {
                      text
                    }
                  }
                }
                nominations {
                  total
                }
                canHaveEpisodes
                imageGallery: images(first: 5) {
                  edges {
                    node {
                      url
                      caption {
                        plainText
                      }
                      width
                      height
                    }
                  }
                }
                trivia(first: 3) {
                  edges {
                    node {
                      text {
                        plainText
                      }
                    }
                  }
                }
                goofs(first: 3) {
                  edges {
                    node {
                      text {
                        plainText
                      }
                    }
                  }
                }

              }
            }""",
            'operationName': 'GetTitle',
            'variables': {
                'id': movie_id
            }
        }
        
      response = requests.post(BASE_URL, headers=HEADERS, json=payload)
      if response.status_code != 200:
          print(f"Response: {response.text}")
      response.raise_for_status()
      return self.format_movie_details(response.json())

  def format_movie_details(self, data):
      """Format movie details for display"""
      title_data = data.get("data", {}).get("title", {})
      if not title_data:
          return None
      
      # Basic info
      movie_id = title_data.get("id")
      title = title_data.get("titleText", {}).get("text")
      original_title = (title_data.get("originalTitleText") or {}).get("text")
      title_type = (title_data.get("titleType") or {}).get("text")
      release_year = (title_data.get("releaseYear") or {}).get("year")
      
      # Release date
      release_date = title_data.get("releaseDate")
      full_release_date = None
      if release_date and isinstance(release_date, dict):
          day = release_date.get("day")
          month = release_date.get("month")
          year = release_date.get("year")
          if year:
              full_release_date = f"{year}-{month or '01'}-{day or '01'}"
      
      # Runtime
      runtime_data = title_data.get("runtime")
      runtime_seconds = runtime_data.get("seconds") if runtime_data else None
      runtime_minutes = runtime_seconds // 60 if runtime_seconds else None
      
      # Ratings
      ratings = title_data.get("ratingsSummary")
      rating = ratings.get("aggregateRating") if ratings else None
      vote_count = ratings.get("voteCount") if ratings else None
      
      # Genres
      genres = []
      genre_data = title_data.get("genres")
      if genre_data and isinstance(genre_data, dict):
          for genre in genre_data.get("genres", []):
              if genre and genre.get("text"):
                  genres.append(genre.get("text"))
      
      # Plot
      plot_data = title_data.get("plot")
      plot = None
      if plot_data and isinstance(plot_data, dict):
          plot_text = plot_data.get("plotText")
          if plot_text and isinstance(plot_text, dict):
              plot = plot_text.get("plainText")
      
      # Image
      primary_image = title_data.get("primaryImage")
      poster_url = primary_image.get("url") if primary_image else None
      image_width = primary_image.get("width") if primary_image else None
      image_height = primary_image.get("height") if primary_image else None
      
      # Certificate
      cert_data = title_data.get("certificate")
      certificate = cert_data.get("rating") if cert_data else None
      
      # Languages
      languages = []
      lang_data = title_data.get("spokenLanguages")
      if lang_data and isinstance(lang_data, dict):
          for lang in lang_data.get("spokenLanguages", []):
              if lang and lang.get("text"):
                  languages.append(lang.get("text"))
      
      # Countries
      countries = []
      country_data = title_data.get("countriesOfOrigin")
      if country_data and isinstance(country_data, dict):
          for country in country_data.get("countries", []):
              if country and country.get("text"):
                  countries.append(country.get("text"))
      
      # Production status
      prod_data = title_data.get("productionStatus")
      production_status = None
      if prod_data and isinstance(prod_data, dict):
          stage_data = prod_data.get("currentProductionStage")
          if stage_data and isinstance(stage_data, dict):
              production_status = stage_data.get("text")
      
      # Series info
      is_series = title_data.get("canHaveEpisodes", False)
      series_data = title_data.get("series")
      series_info = series_data.get("series") if series_data else None
      
      episodes_data = title_data.get("episodes")
      episode_count = None
      if episodes_data and isinstance(episodes_data, dict):
          ep_data = episodes_data.get("episodes")
          if ep_data and isinstance(ep_data, dict):
              episode_count = ep_data.get("total")
      
      # Credits
      credits_by_category = {}
      principal_credits = title_data.get("principalCredits", [])
      for credit_group in principal_credits:
          category = credit_group.get("category", {}).get("text", "Unknown")
          credits = credit_group.get("credits", [])
          
          category_credits = []
          for credit in credits:
              name_info = credit.get("name", {})
              name = name_info.get("nameText", {}).get("text")
              name_id = name_info.get("id")
              
              # Character info for cast
              characters = []
              if "characters" in credit:
                  for char in (credit.get("characters") or []):
                      characters.append(char.get("name"))
              
              if name:
                  profile_image = name_info.get("primaryImage", {}).get("url") if name_info.get("primaryImage") else None
                  credit_info = {
                      "name": name,
                      "id": name_id,
                      "profile_image": profile_image
                  }
                  if characters:
                      credit_info["characters"] = characters
                  category_credits.append(credit_info)
          
          if category_credits:
              credits_by_category[category] = category_credits
      
      # Additional data extraction
      
      # Metacritic score
      metacritic_data = title_data.get("metacritic")
      metascore = None
      if metacritic_data and isinstance(metacritic_data, dict):
          meta_score_data = metacritic_data.get("metascore")
          if meta_score_data and isinstance(meta_score_data, dict):
              metascore = meta_score_data.get("score")
      
      # Image and video counts
      images_data = title_data.get("imageCount")
      image_count = images_data.get("total") if images_data else None
      
      videos_data = title_data.get("videoCount")
      video_count = videos_data.get("total") if videos_data else None
      
      # Company credits
      companies = {}
      company_credits_data = title_data.get("companyCredits")
      if company_credits_data and isinstance(company_credits_data, dict):
          company_credits = company_credits_data.get("edges", [])
          for edge in company_credits:
              if not edge:
                  continue
              node = edge.get("node", {})
              if not node:
                  continue
              company = node.get("company", {})
              if not company:
                  continue
              category_data = node.get("category")
              category = category_data.get("text") if category_data else None
              company_text_data = company.get("companyText")
              company_name = company_text_data.get("text") if company_text_data else None
              company_id = company.get("id")
              
              if category and company_name:
                  if category not in companies:
                      companies[category] = []
                  companies[category].append({
                      "name": company_name,
                      "id": company_id
                  })
      
      # Technical specifications
      tech_specs = title_data.get("technicalSpecifications")
      sound_mixes = []
      aspect_ratios = []
      colorations = []
      
      if tech_specs and isinstance(tech_specs, dict):
          sound_mix_data = tech_specs.get("soundMixes")
          if sound_mix_data and isinstance(sound_mix_data, dict):
              for item in sound_mix_data.get("items", []):
                  if item and item.get("text"):
                      sound_mixes.append(item.get("text"))
          
          aspect_ratio_data = tech_specs.get("aspectRatios")
          if aspect_ratio_data and isinstance(aspect_ratio_data, dict):
              for item in aspect_ratio_data.get("items", []):
                  if item and item.get("aspectRatio"):
                      aspect_ratios.append(item.get("aspectRatio"))
          
          coloration_data = tech_specs.get("colorations")
          if coloration_data and isinstance(coloration_data, dict):
              for item in coloration_data.get("items", []):
                  if item and item.get("text"):
                      colorations.append(item.get("text"))
      
      # Additional comprehensive data
      
      # Meter ranking
      meter_data = title_data.get("meterRanking")
      current_rank = meter_data.get("currentRank") if meter_data else None
      
      # Keywords
      keywords = []
      keyword_data = title_data.get("keywords")
      if keyword_data and isinstance(keyword_data, dict):
          keyword_edges = keyword_data.get("edges", [])
          for edge in keyword_edges[:10]:  # Limit to first 10
              if edge and edge.get("node"):
                  keyword_text = edge["node"].get("text")
                  if keyword_text:
                      keywords.append(keyword_text)
      
      # Trailer information
      trailer_data = title_data.get("latestTrailer")
      trailer = None
      if trailer_data:
          # Extract playback URLs
          playback_urls = trailer_data.get("playbackURLs", [])
          trailer_url = None
          embed_url = None
          
          for playback in playback_urls:
              if playback and playback.get("url"):
                  display_name = playback.get("displayName", {}).get("value", "")
                  if "480p" in display_name or "720p" in display_name:
                      trailer_url = playback.get("url")
                      break
          
          # If no specific quality found, use first available
          if not trailer_url and playback_urls:
              trailer_url = playback_urls[0].get("url")
          
          # Create embed URL from trailer URL if available
          if trailer_url:
              embed_url = trailer_url.replace("https://", "https://www.imdb.com/video/embed/")
          
          trailer = {
              "id": trailer_data.get("id"),
              "name": trailer_data.get("name", {}).get("value") if trailer_data.get("name") else None,
              "url": trailer_url,
              "embedUrl": embed_url,
              "thumbnail": trailer_data.get("thumbnail", {}).get("url") if trailer_data.get("thumbnail") else None,
              "duration": trailer_data.get("runtime", {}).get("value") if trailer_data.get("runtime") else None,
              "uploadDate": trailer_data.get("createdDate"),
              "contentType": trailer_data.get("contentType", {}).get("displayName", {}).get("value") if trailer_data.get("contentType") else None
          }
      
      # Reviews count
      reviews_data = title_data.get("reviews")
      review_count = reviews_data.get("total") if reviews_data else None
      
      # Connected titles (sequels, prequels, etc.)
      connections = []
      connection_data = title_data.get("connections")
      if connection_data and isinstance(connection_data, dict):
          connection_edges = connection_data.get("edges", [])
          for edge in connection_edges:
              if edge and edge.get("node"):
                  node = edge["node"]
                  associated_title = node.get("associatedTitle")
                  if associated_title:
                      connections.append({
                          "id": associated_title.get("id"),
                          "title": associated_title.get("titleText", {}).get("text"),
                          "year": associated_title.get("releaseYear", {}).get("year"),
                          "relationship": node.get("category", {}).get("text")
                      })
      
      # More like this titles
      similar_titles = []
      similar_data = title_data.get("moreLikeThisTitles")
      if similar_data and isinstance(similar_data, dict):
          similar_edges = similar_data.get("edges", [])
          for edge in similar_edges[:5]:  # Limit to first 5
              if edge and edge.get("node"):
                  node = edge["node"]
                  image_data = node.get("primaryImage")
                  poster_url = image_data.get("url") if image_data else None
                  
                  similar_titles.append({
                      "id": node.get("id"),
                      "title": node.get("titleText", {}).get("text"),
                      "year": (node.get("releaseYear") or {}).get("year"),
                      "rating": node.get("ratingsSummary", {}).get("aggregateRating"),
                      "poster_url": poster_url
                  })
      
      # Additional title info
      is_adult = title_data.get("isAdult", False)
      is_ratable = title_data.get("canRate", {}).get("isRatable", False)
      
      # Awards (limited to what's available)
      nominations_data = title_data.get("nominations")
      total_nominations = nominations_data.get("total") if nominations_data else 0
      
      # Image gallery only (videos removed due to API limitations)
      image_gallery = []
      image_data = title_data.get("imageGallery")
      if image_data and isinstance(image_data, dict):
          image_edges = image_data.get("edges", [])
          for edge in image_edges:
              if edge and edge.get("node"):
                  node = edge["node"]
                  image_gallery.append({
                      "url": node.get("url"),
                      "caption": node.get("caption", {}).get("plainText") if node.get("caption") else None,
                      "width": node.get("width"),
                      "height": node.get("height")
                  })
      
      video_gallery = []  # Removed due to API limitations
      
      # Trivia
      trivia_items = []
      trivia_data = title_data.get("trivia")
      if trivia_data and isinstance(trivia_data, dict):
          trivia_edges = trivia_data.get("edges", [])
          for edge in trivia_edges:
              if edge and edge.get("node"):
                  text_data = edge["node"].get("text")
                  if text_data and text_data.get("plainText"):
                      trivia_items.append(text_data["plainText"])
      
      # Goofs
      goof_items = []
      goof_data = title_data.get("goofs")
      if goof_data and isinstance(goof_data, dict):
          goof_edges = goof_data.get("edges", [])
          for edge in goof_edges:
              if edge and edge.get("node"):
                  text_data = edge["node"].get("text")
                  if text_data and text_data.get("plainText"):
                      goof_items.append(text_data["plainText"])
      
      # Removed episode navigation fields due to API limitations
      next_ep_info = None
      prev_ep_info = None
      parent_info = None
      
      # Enhanced actors/directors from credits
      enhanced_actors = []
      enhanced_directors = []
      enhanced_creators = []
      
      for credit_group in principal_credits:
          category = credit_group.get("category", {}).get("text", "")
          credits = credit_group.get("credits", [])
          
          for credit in credits:
              name_info = credit.get("name", {})
              name = name_info.get("nameText", {}).get("text")
              name_id = name_info.get("id")
              profile_image = name_info.get("primaryImage", {}).get("url") if name_info.get("primaryImage") else None
              
              if name:
                  person_data = {
                      "name": name,
                      "url": f"https://www.imdb.com/name/{name_id}/" if name_id else None,
                      "profile_image": profile_image
                  }
                  
                  if category == "Stars":
                      characters = []
                      if "characters" in credit:
                          for char in (credit.get("characters") or []):
                              if char.get("name"):
                                  characters.append(char.get("name"))
                      person_data["characters"] = characters
                      enhanced_actors.append(person_data)
                  elif category == "Director":
                      enhanced_directors.append(person_data)
                  elif category in ["Writers", "Creator"]:
                      person_data["type"] = category
                      enhanced_creators.append(person_data)
      
      # Removed problematic fields due to API limitations
      alt_titles = []
      locations = []
      budget = None
      lifetime_gross = None
      worldwide_gross = None
      opening_weekend = None
      
      # AKAs (Also Known As)
      akas = []
      aka_data = title_data.get("akas")
      if aka_data and isinstance(aka_data, dict):
          aka_edges = aka_data.get("edges", [])
          for edge in aka_edges:
              if not edge:
                  continue
              node = edge.get("node", {})
              if not node:
                  continue
              title_text = node.get("text")
              country_data = node.get("country")
              country_text = country_data.get("text") if country_data else None
              
              if title_text:
                  akas.append({
                      "title": title_text,
                      "country": country_text
                  })
      
      return {
          "id": movie_id,
          "title": title,
          "original_title": original_title,
          "title_type": title_type,
          "release_year": release_year,
          "release_date": full_release_date,
          "runtime_minutes": runtime_minutes,
          "rating": rating,
          "vote_count": vote_count,
          "metascore": metascore,
          "genres": genres,
          "plot": plot,
          "poster_url": poster_url,
          "image_dimensions": {"width": image_width, "height": image_height} if image_width and image_height else None,
          "image_count": image_count,
          "video_count": video_count,
          "certificate": certificate,
          "languages": languages,
          "countries": countries,
          "production_status": production_status,
          "is_series": is_series,
          "series_info": series_info,
          "episode_count": episode_count,
          "credits": credits_by_category,
          "companies": companies,
          "technical_specs": {
              "sound_mixes": sound_mixes,
              "aspect_ratios": aspect_ratios,
              "colorations": colorations
          },
          "akas": akas,
          "current_rank": current_rank,
          "keywords": keywords,
          "trailer": trailer,
          "review_count": review_count,
          "enhanced_actors": enhanced_actors,
          "enhanced_directors": enhanced_directors,
          "enhanced_creators": enhanced_creators,
          "imdb_url": f"https://www.imdb.com/title/{movie_id}/" if movie_id else None,
          "connections": connections,
          "similar_titles": similar_titles,
          "is_adult": is_adult,
          "is_ratable": is_ratable,
          "total_nominations": total_nominations,
          "image_gallery": image_gallery,
          "trivia_items": trivia_items,
          "goof_items": goof_items

      }

  def get_streaming_availability(self, title_id):
      """Get streaming availability for a single title ID"""
      
      url = "https://api.graphql.imdb.com/"
      
      variables = {
          "id": title_id
      }
      
      query = """
      query HERO_WATCH_BOX($id: ID!) {
        title(id: $id) {
          primaryWatchOption {
            additionalWatchOptionsCount
            watchOption {
              provider {
                name {
                  value
                }
                refTagFragment
              }
              link(platform: WEB)
              title {
                value
              }
              description {
                value
              }
              promoted
            }
          }
          watchOptionsByCategory {
            categorizedWatchOptionsList {
              categoryName {
                value
              }
              watchOptions {
                title {
                  value
                }
                shortDescription {
                  value
                }
                link(platform: WEB)
                provider {
                  id
                  logos {
                    slate {
                      url
                      height
                      width
                    }
                  }
                  refTagFragment
                }
              }
            }
          }
        }
      }
      """
      
      payload = {
          "operationName": "HERO_WATCH_BOX",
          "query": query,
          "variables": variables
      }
      
      headers = {
          "accept": "application/graphql+json, application/json",
          "content-type": "application/json",
          "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36",
          "Referer": "https://www.imdb.com/",
          "x-imdb-user-country": "US",
          "x-imdb-user-language": "en-US"
      } 
      response = requests.post(url, json=payload, headers=headers)

      data = (response.json().get("data") or {}).get("title")  
      by_category = (data.get("watchOptionsByCategory") or {}).get("categorizedWatchOptionsList", []) if data else []  
      categories = [] 

      for category in by_category:

          provider_category = category.get("categoryName", {}).get("value")
          options = category.get("watchOptions", []) 

          for option in options:
              
              provider_code = (option.get("provider") or {}).get("id", {})
              provider_name = (option.get("provider") or {}).get("refTagFragment", {})
              provider_image = (option.get("provider") or {}).get("logos", {}).get("slate", {}).get("url")
              provider_image_height = (option.get("provider") or {}).get("logos", {}).get("slate", {}).get("height")
              provider_image_width = (option.get("provider") or {}).get("logos", {}).get("slate", {}).get("width")
              provider_title = option.get("title", {}).get("value")
              provider_desc = (option.get("shortDescription") or {}).get("value")
              provider_link = option.get("link")   

              categories.append({
                  "provider_code": provider_code, 
                  "provider_name": provider_name, 
                  "provider_image": provider_image,
                  "provider_image_height": provider_image_height,
                  "provider_image_width": provider_image_width,
                  "provider_title": provider_title,
                  "provider_desc": provider_desc,
                  "provider_link": provider_link,
                  "provider_category": provider_category
                })
 
      if response.status_code == 200:
          return categories 
      else:
          print(f"Error: {response.status_code}")
          print(f"Response: {response.text}")
          return None

  def upsert_image_assets(self, media_id, media):
      dims = media.get("image_dimensions") or {}
      source_url = media.get("poster_url")

      if not source_url:
        return {
            "media_id": media_id,
            "image_kind": "poster",
            "image_size": "original",
            "source_provider": "imdb" if media.get("imdb_url") else None,
            "source_url": None,
            "width": dims.get("width"),
            "height": dims.get("height"),
            "status": "skipped",
            "error_message": "No poster_url found",
        }

      return {
        "media_id": media["id"],
        "image_kind": "poster",
        "image_size": "original",
        "source_provider": "imdb" if media.get("imdb_url") else "unknown",
        "source_url": source_url,
        "width": dims.get("width"),
        "height": dims.get("height"),
        "status": "pending",
      }

  # def save_trending_data(data, filename):
  #     """Save trending data to JSON file"""
  #     with open(filename, 'w', encoding='utf-8') as f:
  #         json.dump(data, f, indent=2, ensure_ascii=False)
  #     print(f"Trending data saved to {filename}")

  # def main():
  #     parser = argparse.ArgumentParser(description="Download trending movies from IMDb")
  #     parser.add_argument("-c", "--count", type=int, default=8, help="Number of trending movies to fetch (default: 8)")
  #     parser.add_argument("-w", "--window", default="HOURS", choices=["HOURS", "DAYS", "WEEKS"], 
  #                         help="Data window for trending (default: HOURS)")
  #     parser.add_argument("-o", "--output", default="trending_movies.json", 
  #                         help="Output filename (default: trending_movies.json)")
  #     parser.add_argument("--ids-only", action="store_true", 
  #                         help="Only extract and display movie IDs")
      
  #     args = parser.parse_args()
      
  #     print(f"Fetching top {args.count} trending movies...")
      
  #     try:
  #         data = get_trending_movies(count=args.count, data_window=args.window)
          
  #         if args.ids_only:
  #             movie_ids = extract_movie_ids(data)
  #             print("\nTrending Movie IDs:")
  #             for movie in movie_ids:
  #                 print(f"{movie['rank']}. {movie['id']} - {movie['title']} ({movie.get('release_year', 'N/A')})")
  #         else:
  #             save_trending_data(data, args.output)
              
  #             # Display trending movies
  #             movie_ids = extract_movie_ids(data)
  #             print(f"\nTop {len(movie_ids)} Trending Movies:")
  #             for movie in movie_ids:
  #                 print(f"\n{movie['rank']}. {movie['title']} ({movie['id']})")
  #                 if movie.get('original_title') and movie['original_title'] != movie['title']:
  #                     print(f"   Original Title: {movie['original_title']}")
  #                 if movie.get('title_type'):
  #                     print(f"   Type: {movie['title_type']}")
  #                 if movie.get('release_year'):
  #                     print(f"   Year: {movie['release_year']}")
  #                 if movie.get('runtime_minutes'):
  #                     print(f"   Runtime: {movie['runtime_minutes']} minutes")
  #                 if movie.get('rating'):
  #                     print(f"   Rating: {movie['rating']}/10 ({movie.get('vote_count', 0)} votes)")
  #                 if movie.get('genres'):
  #                     print(f"   Genres: {', '.join(movie['genres'])}")
  #                 if movie.get('plot'):
  #                     plot_preview = movie['plot'][:100] + "..." if len(movie['plot']) > 100 else movie['plot']
  #                     print(f"   Plot: {plot_preview}")
                  
  #                 # Show credits by category
  #                 credits = movie.get('credits', {})
  #                 for category, people in credits.items():
  #                     names = [person['name'] for person in people[:3]]  # Show first 3
  #                     if names:
  #                         print(f"   {category}: {', '.join(names)}")
                  

      
  #     except Exception as e:
  #         print(f"Error fetching trending movies: {e}")

  # if __name__ == "__main__":
  #     main()
