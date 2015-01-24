from collections import namedtuple
from datetime import datetime
import os
import shutil

import yaml

from photoshell.util import dict_to_tuple
from photoshell.util import tuple_to_dict
from rawphoto.raw import Raw


common_formats = ['.PNG', '.JPG', '.JPEG']

_Photo = namedtuple('Photo', [
    'aperture',
    'datetime',
    'developed_path',
    'exposure',
    'flash',
    'focal_length',
    'gps',
    'file_hash',
    'height',
    'iso',
    'lens',
    'make',
    'model',
    'orientation',
    'raw_path',
    'width',
])


class Photo(_Photo):

    # TODO: move this off the class
    def gtk_image(self, base_path, max_width=1280, max_height=1024):
        from photoshell.image import Image
        return Image(self.developed_path, self.datetime).load_preview(
            base_path,
            max_width=max_width,
            max_height=max_height,
        )

    # TODO: move this off the class
    def gtk_pixbuf(self, base_path, max_width=1280, max_height=1024):
        from photoshell.image import Image
        return Image(self.developed_path, self.datetime).load_pixbuf(
            base_path,
            max_width=max_width,
            max_height=max_height,
        )

    @classmethod
    def load(cls, photo_path, file_hash=None):
        sidecar_path = photo_path + '.yaml'

        if os.path.isfile(sidecar_path):
            with open(sidecar_path, 'r') as sidecar:
                metadata = yaml.load(sidecar)
        else:
            with Raw(filename=photo_path) as raw:
                metadata = raw.metadata

        # Don't trust the metadata; always use our own path and hash.
        metadata['raw_path'] = photo_path
        metadata['file_hash'] = file_hash

        # TODO: rawphoto doesn't return the data in the same format as the
        # sidecar
        if type(metadata['datetime']) is str:
            metadata['datetime'] = datetime.strptime(
                metadata['datetime'], "%Y:%m:%d %H:%M:%S")

        return dict_to_tuple(Photo, metadata)

    def copy(self, new_path, delete_originals=False):
        # copy photo
        existing_photo_path = self.raw_path
        shutil.copyfile(existing_photo_path, new_path)
        # TODO: Make sure the file copied w/o errors first?
        if delete_originals:
            os.unlink(existing_photo_path)

        # copy metadata
        existing_meta_path = self.raw_path + '.yaml'
        if os.path.exists(existing_meta_path):
            shutil.copyfile(existing_meta_path, new_path + '.yaml')
            # TODO: Make sure the file copied w/o errors first?
            if delete_originals:
                os.unlink(existing_meta_path)

        photo_dict = tuple_to_dict(self)
        photo_dict['raw_path'] = new_path
        return dict_to_tuple(Photo, photo_dict)

    def develop(self, write_sidecar=False, cache_path=None):
        # develop photow
        if os.path.splitext(self.raw_path)[-1].upper() in common_formats:
            developed_path = self.raw_path
        else:
            developed_name = '{file_hash}.{extension}'.format(
                file_hash=self.file_hash,
                extension='jpg',
            )

            developed_path = os.path.join(
                cache_path,
                'jpg',
                developed_name,
            )

        if not os.path.isfile(developed_path):
            blob = Raw(filename=self.raw_path).fhandle.get_quarter_size_rgb()

            with open(developed_path, 'wb') as f:
                f.write(blob)

        photo_dict = tuple_to_dict(self)
        photo_dict['developed_path'] = developed_path
        photo = dict_to_tuple(Photo, photo_dict)

        if write_sidecar:
            meta_path = photo.raw_path + '.yaml'
            # TODO: merge existing metadata
            # This is an odd edge case where you're importing from "source" to
            # "destination" and "destination" already has a sidecar for some
            # reason. Sidecars from "source" will be loaded in already.
            with open(meta_path, 'w+') as meta_file:
                yaml.dump(
                    tuple_to_dict(photo), meta_file, default_flow_style=False)

        return photo

    def __eq__(self, other):
        return self.file_hash == other.file_hash
