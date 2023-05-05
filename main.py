import json
import os
import requests
from bs4 import BeautifulSoup
from colorama import Fore
from PIL import Image
from fpdf import FPDF
import re
import tempfile

BASE_URL = 'https://ww5.mangakakalot.tv/'


def search_manga(query):
    # replace spaces witth %20
    query = query.replace(' ', '%20')

    url = BASE_URL + 'search/' + query
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # get all the manga titles from the class panel_story_list
    manga_list = soup.find_all('div', class_='story_item')
    list_manga = []

    if (len(manga_list) == 0):
        print('No manga found!')
        return list_manga

    for manga in manga_list:
        manga_title = manga.find('h3').find('a').get_text()
        manga_link = manga.find('a')['href']
        list_manga.append((manga_title, manga_link))
    return list_manga


def select_chapter(url):
    url = BASE_URL + url
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    soup = soup.find_all('div', class_='chapter-list')
    # get all row class of the soup
    chapter_list = soup[0].find_all('div', class_='row')
    list_chapter = []

    for chapter in chapter_list:
        chapter_title = chapter.find('a').get_text()
        chapter_link = chapter.find('a')['href']
        list_chapter.append((chapter_title, chapter_link))

    return list_chapter


def open_chapter(url):
    url = BASE_URL + url
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    soup = soup.find_all('div', class_='vung-doc')
    # get all row class of the soup
    chapter_list = soup[0].find_all('img')
    list_chapter = []

    for chapter in chapter_list:
        chapter_title = chapter['title']
        chapter_link = chapter['data-src']
        list_chapter.append((chapter_link))
    return list_chapter

# merge all the images in a pdf file with PyPDF2 and open it with the default pdf reader


def merge_images(list_images, pdf_name):
    # download all the images in the list
    for image in list_images:
        response = requests.get(image)
        with open(image.split('/')[-1], 'wb') as f:
            f.write(response.content)

    pdf = FPDF()
    for image in list_images:
        # conserve the ratio of the image
        cover = Image.open(image.split('/')[-1])
        width, height = cover.size
        width, height = float(width * 0.264583), float(height * 0.264583)
        pdf.add_page(format=(width, height))
        pdf.image(image.split('/')[-1], 0, 0, width, height)
    name = remove_special_characters(pdf_name)
    name = pdf_name + '.pdf'
    print('The pdf file is ready!', name)
    pdf.output(name)
    os.startfile(name)


def remove_special_characters(string):
    pattern = r'[^\W_]'
    string = re.sub(pattern, ' ', string)
    string = string.strip()
    print(string)
    return string


def main():
    print('Please enter the name of the manga you want to read: ')
    manga_title = input()
    result = search_manga(manga_title)
    for i in range(len(result)):
        # alternate the color of the result
        index = i+1
        if i % 2 == 0:
            print(Fore.GREEN + str(index) + ') ' + result[i][0])
        else:
            print(Fore.YELLOW + str(index) + ') ' + result[i][0])

    print(Fore.WHITE + 'Please enter the number of the manga you want to read: ')
    manga_number = int(input()) - 1

    chapter = select_chapter(result[manga_number][1])
    chapter.reverse()
    print(Fore.BLUE + 'Please enter the number of the chapter you want to read. 1-' +
          str(len(chapter)) + ': ')

    chapter_number = int(input()) - 1
    images = open_chapter(chapter[chapter_number][1])
    print('Please wait while the images are being downloaded...')
    merge_images(images, result[manga_number][0] +
                 ' ' + str(chapter_number+1))

    # Ask for user options
    while True:
        print(Fore.WHITE + 'Enter s to search a new manga, n for next chapter, p for previous chapter,'
              ' S for select a specific episode, or q to quit:')
        option = input().lower()
        track_chapter(manga_title, chapter_number, chapter)
        if option == 's':
            print('Please enter the name of the manga you want to read: ')
            manga_title = input()
            result = search_manga(manga_title)
            for i in range(len(result)):
                # alternate the color of the result
                index = i+1
                if i % 2 == 0:
                    print(Fore.GREEN + str(index) + ') ' + result[i][0])
                else:
                    print(Fore.YELLOW + str(index) + ') ' + result[i][0])

            print(Fore.WHITE + 'Please enter the number of the manga you want to read: ')
            manga_number = int(input()) - 1

            chapter = select_chapter(result[manga_number][1])
            chapter.reverse()
            print(Fore.BLUE + 'Please enter the number of the chapter you want to read. 1-' +
                  str(len(chapter)) + ': ')

            chapter_number = int(input()) - 1
            images = open_chapter(chapter[chapter_number][1])
            print('Please wait while the images are being downloaded...')
            merge_images(images, result[manga_number][0] +
                         ' ' + str(chapter_number+1))

        elif option == 'n':
            if chapter_number == len(chapter) - 1:
                print('This is the last chapter.')
            else:
                chapter_number += 1
                images = open_chapter(chapter[chapter_number][1])
                print('Please wait while the images are being downloaded...')
                merge_images(images, result[manga_number][0] +
                             ' ' + str(chapter_number+1))

        elif option == 'p':
            if chapter_number == 0:
                print('This is the first chapter.')
            else:
                chapter_number -= 1
                images = open_chapter(chapter[chapter_number][1])
                print('Please wait while the images are being downloaded...')
                merge_images(images, result[manga_number][0] +
                             ' ' + str(chapter_number+1))

        elif option == 's':
            print(Fore.WHITE + 'Please enter the number of the chapter you want to read. 1-' +
                  str(len(chapter)) + ': ')
            manga_title = input()
            chapter_number = int(input()) - 1
            images = open_chapter(chapter[chapter_number][1])
            merge_images(images, result[manga_number][0] +
                         ' ' + str(chapter_number+1))

        elif option == 'q':
            break

        else:
            print('Please enter a valid option.')

    print('Thank you for using the program!')
    exit()


def track_chapter(manga_title, chapter_number, chapters_link):
    # verify if the file user_data.json exists
    if not os.path.isfile('user_data.json'):
        user_data = {}
        # create the file if it doesn't exist
        with open('user_data.json', 'w') as f:
            json.dump(user_data, f)
        return False

    with open('user_data.json', 'r') as f:
        user_data = json.load(f)
        titles = user_data.keys()
        if manga_title not in titles:
            user_data[manga_title] = [chapter_number, chapters_link]
        else:
            user_data[manga_title][0] = chapter_number

        with open('user_data.json', 'w') as f:
            json.dump(user_data, f)


def read_manga_from_history():
    # verify if the file user_data.json exists
    if not os.path.isfile('user_data.json'):
        print('You have no history.')
        return False
    print('Please chose a manga from your history:')
    with open('user_data.json', 'r') as f:
        # show only the titles of the mangas
        user_data = json.load(f)
        keys = user_data.keys()
        for i in range(len(keys)):
            print(str(i+1) + ') ' + list(keys)[i])
        title = input()
        # verify if the input is valid
        if title.isdigit():
            title = int(title)
            if title > len(keys) or title < 1:
                print('Please enter a valid number.')
                return False
            title = list(keys)[title-1]
            # get the last chapter read
            chapter = user_data[title][0] + 1
            # get the link of the chapters
            chapters_link = user_data[title][1]
            # open the chapter
            images = open_chapter(chapters_link[chapter][1])
            merge_images(images, title + ' ' + str(chapter))

        else:
            print('Please enter a valid number.')
            return False


read_manga_from_history()
# if __name__ == '__main__':
#     main()
