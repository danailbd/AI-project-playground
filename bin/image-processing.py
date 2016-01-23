import json
from functools import reduce
import sys, getopt
from os import walk
import os.path as path

"""
tags extraction
- avg of image conf
- predefined
- tags with confidence
"""

class ImageModel:
    def __init__(self, image_id, tags_list):
        self.id = image_id
        self.tagsList = tags_list

    def set_image_data(self, image_id, tags_list):
        self.id = image_id
        self.tagsList = tags_list


class ImageProcessor:
    @staticmethod
    def process(image_json_path, min_confidence=0):
        """
        Reads the json files passed
        Expected json:
        {'image': ... , 'tags': [{'tag': '...', 'confidence': 0.0}, ...]}

        :param image_json_path:  The path to the json file containing the tags data
        :param min_confidence:   ??
        :return: Image model
        """

        def process_tags(tags_list):
            sum_conf = lambda tag1, tag2: tag1 + tag2['confidence']
            average_confidence = reduce(sum_conf, tags_list, 0) / len(tags_list)

            tags_to_use = list(filter(lambda x: x['confidence'] > average_confidence, tags_list))

            return tags_to_use

        with open(image_json_path) as image_file:
            # returns array of 1 element
            parsed_image = json.load(image_file)

        image_data = parsed_image['results'][0]
        image_id = image_data['image']
        image_tags = image_data['tags']

        useful_tags = process_tags(image_tags)

        return ImageModel(image_id, useful_tags)


class ClipModel:
    def __init__(self, clip_id, tags_map):
        self.id = clip_id
        self.tagsCountMap = tags_map

    def get_as_dict(self):
            return self.__dict__


class ClipProcessor:
    def __init__(self):
        self.image_processor = ImageProcessor()

    def process(self, clip_folder):
        def process_tags(image_tags, image_map):
            for tag_data in image_tags:
                tag = tag_data['tag']
                image_map.append(tag)
                return
                if image_map.get(tag):
                    image_map[tag] += 1
                else:
                    image_map[tag] = 1

        # TODO add some checks
        clip_tags_map = []
        for (dir, dirs, files) in walk(clip_folder):
            for file_name in files:
                image_model = self.image_processor.process(path.join(dir, file_name))
                # add tags to the bag of words
                process_tags(image_model.tagsList, clip_tags_map)
        clip_id = path.basename(clip_folder)
        return ClipModel(clip_id, clip_tags_map)


class CategoryModel:
# TODO add category Id - dir name ?
    def __init__(self, clips_data, category_id):
        """
        :param clips_data: list of the clips in the category
        :type clips_data: list[ClipModel]
        :return:
        """
        self.id = category_id
        self.clips_data = clips_data

    def get_as_dict(self):
        clips_list = []
        for clip_model in self.clips_data:
            clips_list.append(clip_model.get_as_dict())
        self_dict = self.__dict__
        self_dict['clips_data'] = clips_list
        return self_dict


class CategoryProcessor:
    def __init__(self):
        self.clip_processor = ClipProcessor()

    def process(self, category_folder):
        category_clips = []
        for (dir, dirs, files) in walk(category_folder):
            processed = 1
            for clip_folder in dirs:
                print('Processing clip file: ', clip_folder)
                print(processed, '/', len(dirs))
                clip_model = self.clip_processor.process(path.join(dir, clip_folder))
                category_clips.append(clip_model)
                processed += 1
        return CategoryModel(category_clips, path.basename(category_folder))

# TODO process path - folder/cat/clip


class FolderModel:
    def __init__(self, categories):
        """
        """
        self.categories = categories

    def get_as_dict(self):
        categories = []
        for category_model in self.categories:
            categories.append(category_model.get_as_dict())
        return categories


class FolderProcessor:
    """
    Processes folder containing categories
    """
    def __init__(self):
        self.category_processor = CategoryProcessor()

    def process(self, folder):
        categories = []
        for (dir, dirs, files) in walk(folder):
            processed = 1
            for category_folder in dirs:
                print(processed, '/', len(dirs), category_folder)
                clip_model = self.category_processor.process(path.join(dir, category_folder))
                categories.append(clip_model)
        return FolderModel(categories)


def main(argv):
    print(argv)
    try:
        opts, args = getopt.getopt(argv,
                                   "C:c:i:d:D:",
                                   ["category", "clip", "image"])
    except getopt.GetoptError:
        print('test.py -C path/to/categoryFiles; -c path/to/clipFolders')
        sys.exit(2)

    print('Processing folder ...', opts, args)
    data_for_save = None
    processor = None
    process_folder = None
    destination_folder = ''
    for opt, arg in opts:
        print(opt, arg)
        if opt == '-D':
            # returns list of categories
            process_folder = arg
            processor = FolderProcessor()
        elif opt == '-C':
            process_folder = arg
            processor = CategoryProcessor()
        elif opt == '-c':
            process_folder = arg
            processor = ClipProcessor()
        elif opt == '-i':
            process_folder = arg
            processor = ImageProcessor()
        elif opt == '-d':
            destination_folder = arg

    # save data to file
    data_for_save = processor.process(process_folder)
    data_for_save = data_for_save.get_as_dict()
    if not isinstance(data_for_save, list):
        data_for_save = [data_for_save]
    for item in data_for_save:
        destination_path = path.join(destination_folder, item['id'] + '.json')
        print('Save to : ', destination_path)
        with open(destination_path, 'w+') as fp:
            json.dump(item, fp)

if __name__ == "__main__":
    main(sys.argv[1:])

