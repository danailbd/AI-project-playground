import json
from functools import reduce
import sys, getopt
from os import walk
import os.path as path
import os

"""
tags extraction
- avg of image conf
- predefined
- tags with confidence
"""


class ImageModel:

    def __init__(self, image_id, tags_list, average_confidance):
        self.id = image_id
        self.tagsList = tags_list
        self.confidance = average_confidance

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

            # currently no change in tags list
            return (tags_list, average_confidence)

        with open(image_json_path) as image_file:
            # returns array of 1 element
            parsed_image = json.load(image_file)

        image_data = parsed_image['results'][0]
        image_id = image_data['image']
        image_tags = image_data['tags']
        
        useful_tags, average_confidance = process_tags(image_tags)

        return ImageModel(image_id, useful_tags, average_confidance)


class ClipModel:
    def __init__(self, clip_id, tags_map, average_confidance):
        self.id = clip_id
        self.tagsCountMap = tags_map
        self.confidance = average_confidance

    def get_as_dict(self):
            return self.__dict__


class ClipProcessor:
    def __init__(self):
        self.image_processor = ImageProcessor()


    def process(self, clip_folder, min_confidence=15):
        def process_tags(image_tags, image_map):
            for tag_data in image_tags:
                confidence = tag_data['confidence']
                tag = tag_data['tag']
                if confidence > min_confidence:
                    image_map.append(tag)

        # TODO add some checks
        clip_tags_list = []
        images_count = 0
        total_tags_count = 0
        for (dir, dirs, files) in walk(clip_folder):
            average_confidance = 0
            images_count = len(files)
            for file_name in files:
                image_model = self.image_processor.process(path.join(dir, file_name), 0.3)
                # add tags to the bag of words
                process_tags(image_model.tagsList, clip_tags_list)

                total_tags_count += len(image_model.tagsList)
                average_confidance += image_model.confidance / images_count
        clip_id = path.basename(clip_folder)

        print('Tags count - ', clip_id, ' : ', len(clip_tags_list), '|', total_tags_count)
        return ClipModel(clip_id, clip_tags_list, average_confidance)


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

    def process(self, category_folder, min_confidence=0.5, logging=False):
        category_clips = []
        clips_count = 0
        average_confidance = 0
        for (dir, dirs, files) in walk(category_folder):
            processed = 1
            clip_count = len(dirs)
            for clip_folder in dirs:
                if logging:
                    print('Processing clip file: ', clip_folder)
                    print(processed, '/', len(dirs))
                clip_model = self.clip_processor.process(path.join(dir, clip_folder))
                # Filter tags by some constant
                if clip_model.confidance > min_confidence:
                    category_clips.append(clip_model)
                average_confidance += clip_model.confidance / clip_count
                processed += 1
        print(path.basename(category_folder), ': ',  average_confidance)
        print('Clips count', len(category_clips), '|', clips_count)
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
    def __init__(self, folder):
        self.category_processor = CategoryProcessor()
        walked_folder = walk(folder)
# (dir, dirs, files)
        self.dir = folder
        self.dirs = next(walked_folder)[1]
        self.dirs_count = len(self.dirs)

    def remaining_count(self):
        return len(self.dirs)

    def process(self):
        categories = []
        processed = 1
        for category_folder in self.dirs:
            print(processed, '/', len(self.dirs), category_folder)
            clip_model = self.category_processor.process(path.join(dir, category_folder))
            categories.append(clip_model)
        return FolderModel(categories)

    def process_one(self):
        category_folder = self.dirs.pop(0)
        processing = self.dirs_count - len(self.dirs)
        print(processing, '/', self.dirs_count, category_folder)
        category_model = self.category_processor.process(path.join(self.dir, category_folder))
        return category_model


def main(argv):
    print(argv)
    try:
        opts, args = getopt.getopt(argv,
                                   "C:c:i:d:f:",
                                   ["category", "clip", "image"])
    except getopt.GetoptError:
        print('test.py -C path/to/categoryFiles -d path/for/save/; -c path/to/clipFolders')
        sys.exit(2)

    print('Processing folder ...', opts, args)
    data_for_save = None
    processor = None
    process_folder = None
    destination_folder = ''
    for opt, arg in opts:
        print(opt, arg)
        if opt == '-f':
            process_folder = arg
            processor = FolderProcessor(process_folder)
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
            # create path if not exists
            if not os.path.exists(os.path.dirname(destination_folder)):
                try:
                    print('try try')
                    os.makedirs(os.path.dirname(destination_folder))
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise
# TODO fix for all -- added process_one

    def save_parsed_data_to_file(data):
        data = data.get_as_dict()
        # save data to file
        if not isinstance(data, list):
            data = [data]
        for item in data:
            destination_path = path.join(destination_folder, item['id'] + '.json')
            print('Save to : ', destination_path)
            with open(destination_path, 'w+') as fp:
                json.dump(item, fp)

    if callable(getattr(processor, 'process_one', None)):
        while processor.remaining_count() > 0:
            data_for_save = processor.process_one()
            save_parsed_data_to_file(data_for_save)
    else:
        save_parsed_data_to_file(data_for_save)
        
if __name__ == "__main__":
    main(sys.argv[1:])

