from impact.utils import any_typ, ByPassTypeTuple, make_3d_mask
import comfy_extras.nodes_mask
from nodes import MAX_RESOLUTION
import torch
import comfy
import sys
import nodes


class GeneralSwitch:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                    "select": ("INT", {"default": 1, "min": 1, "max": 999999, "step": 1}),
                    "sel_mode": ("BOOLEAN", {"default": True, "label_on": "select_on_prompt", "label_off": "select_on_execution", "forceInput": False}),
                    },
                "optional": {
                    "input1": (any_typ,),
                    },
                "hidden": {"unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO"}
                }

    RETURN_TYPES = (any_typ, "STRING", "INT")
    RETURN_NAMES = ("selected_value", "selected_label", "selected_index")
    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Util"

    def doit(self, *args, **kwargs):
        selected_index = int(kwargs['select'])
        input_name = f"input{selected_index}"

        selected_label = input_name
        node_id = kwargs['unique_id']

        if 'extra_pnginfo' in kwargs and kwargs['extra_pnginfo'] is not None:
            nodelist = kwargs['extra_pnginfo']['workflow']['nodes']
            for node in nodelist:
                if str(node['id']) == node_id:
                    inputs = node['inputs']

                    for slot in inputs:
                        if slot['name'] == input_name and 'label' in slot:
                            selected_label = slot['label']

                    break
        else:
            print(f"[Impact-Pack] The switch node does not guarantee proper functioning in API mode.")

        if input_name in kwargs:
            return (kwargs[input_name], selected_label, selected_index)
        else:
            print(f"ImpactSwitch: invalid select index (ignored)")
            return (None, "", selected_index)


class LatentSwitch:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                    "select": ("INT", {"default": 1, "min": 1, "max": 99999, "step": 1}),
                    "latent1": ("LATENT",),
                    },
                }

    RETURN_TYPES = ("LATENT", )

    OUTPUT_NODE = True

    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Util"

    def doit(self, *args, **kwargs):
        input_name = f"latent{int(kwargs['select'])}"

        if input_name in kwargs:
            return (kwargs[input_name],)
        else:
            print(f"LatentSwitch: invalid select index ('latent1' is selected)")
            return (kwargs['latent1'],)


class ImageMaskSwitch:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "select": ("INT", {"default": 1, "min": 1, "max": 4, "step": 1}),
            "images1": ("IMAGE",),
        },

            "optional": {
                "mask1_opt": ("MASK",),
                "images2_opt": ("IMAGE",),
                "mask2_opt": ("MASK",),
                "images3_opt": ("IMAGE",),
                "mask3_opt": ("MASK",),
                "images4_opt": ("IMAGE",),
                "mask4_opt": ("MASK",),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK",)

    OUTPUT_NODE = True

    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Util"

    def doit(self, select, images1, mask1_opt=None, images2_opt=None, mask2_opt=None, images3_opt=None, mask3_opt=None,
             images4_opt=None, mask4_opt=None):
        if select == 1:
            return images1, mask1_opt,
        elif select == 2:
            return images2_opt, mask2_opt,
        elif select == 3:
            return images3_opt, mask3_opt,
        else:
            return images4_opt, mask4_opt,


class GeneralInversedSwitch:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                    "select": ("INT", {"default": 1, "min": 1, "max": 999999, "step": 1}),
                    "input": (any_typ,),
                    },
                "hidden": {"unique_id": "UNIQUE_ID"},
                }

    RETURN_TYPES = ByPassTypeTuple((any_typ, ))
    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Util"

    def doit(self, select, input, unique_id):
        res = []

        for i in range(0, select):
            if select == i+1:
                res.append(input)
            else:
                res.append(None)

        return res


class RemoveNoiseMask:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"samples": ("LATENT",)}}

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Util"

    def doit(self, samples):
        res = {key: value for key, value in samples.items() if key != 'noise_mask'}
        return (res, )


class ImagePasteMasked:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "destination": ("IMAGE",),
                "source": ("IMAGE",),
                "x": ("INT", {"default": 0, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
                "y": ("INT", {"default": 0, "min": 0, "max": MAX_RESOLUTION, "step": 1}),
                "resize_source": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "mask": ("MASK",),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "composite"

    CATEGORY = "image"

    def composite(self, destination, source, x, y, resize_source, mask = None):
        destination = destination.clone().movedim(-1, 1)
        output = comfy_extras.nodes_mask.composite(destination, source.movedim(-1, 1), x, y, mask, 1, resize_source).movedim(1, -1)
        return (output,)


from impact.utils import any_typ

class ImpactLogger:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                        "data": (any_typ, ""),
                    },
                "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
                }

    CATEGORY = "ImpactPack/Debug"

    OUTPUT_NODE = True

    RETURN_TYPES = ()
    FUNCTION = "doit"

    def doit(self, data, prompt, extra_pnginfo):
        shape = ""
        if hasattr(data, "shape"):
            shape = f"{data.shape} / "

        print(f"[IMPACT LOGGER]: {shape}{data}")

        print(f"         PROMPT: {prompt}")

        # for x in prompt:
        #     if 'inputs' in x and 'populated_text' in x['inputs']:
        #         print(f"PROMP: {x['10']['inputs']['populated_text']}")
        #
        # for x in extra_pnginfo['workflow']['nodes']:
        #     if x['type'] == 'ImpactWildcardProcessor':
        #         print(f" WV : {x['widgets_values'][1]}\n")

        return {}


class ImpactDummyInput:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {}}

    CATEGORY = "ImpactPack/Debug"

    RETURN_TYPES = (any_typ,)
    FUNCTION = "doit"

    def doit(self):
        return ("DUMMY",)


class MasksToMaskList:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                        "masks": ("MASK", ),
                      }
                }

    RETURN_TYPES = ("MASK", )
    OUTPUT_IS_LIST = (True, )
    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Operation"

    def doit(self, masks):
        if masks is None:
            empty_mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            return ([empty_mask], )

        res = []

        for mask in masks:
            res.append(mask)

        print(f"mask len: {len(res)}")

        res = [make_3d_mask(x) for x in res]

        return (res, )


class MaskListToMaskBatch:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                        "mask": ("MASK", ),
                      }
                }

    INPUT_IS_LIST = True

    RETURN_TYPES = ("MASK", )
    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Operation"

    def doit(self, mask):
        if len(mask) == 1:
            mask = make_3d_mask(mask[0])
            return (mask,)
        elif len(mask) > 1:
            mask1 = make_3d_mask(mask[0])

            for mask2 in mask[1:]:
                mask2 = make_3d_mask(mask2)
                if mask1.shape[1:] != mask2.shape[1:]:
                    mask2 = comfy.utils.common_upscale(mask2.movedim(-1, 1), mask1.shape[2], mask1.shape[1], "lanczos", "center").movedim(1, -1)
                mask1 = torch.cat((mask1, mask2), dim=0)

            return (mask1,)
        else:
            empty_mask = torch.zeros((1, 64, 64), dtype=torch.float32, device="cpu").unsqueeze(0)
            return (empty_mask,)


class ImageListToImageBatch:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                        "images": ("IMAGE", ),
                      }
                }

    INPUT_IS_LIST = True

    RETURN_TYPES = ("IMAGE", )
    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Operation"

    def doit(self, images):
        if len(images) <= 1:
            return (images,)
        else:
            image1 = images[0]
            for image2 in images[1:]:
                if image1.shape[1:] != image2.shape[1:]:
                    image2 = comfy.utils.common_upscale(image2.movedim(-1, 1), image1.shape[2], image1.shape[1], "lanczos", "center").movedim(1, -1)
                image1 = torch.cat((image1, image2), dim=0)
            return (image1,)


class ImageBatchToImageList:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image": ("IMAGE",), }}

    RETURN_TYPES = ("IMAGE",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Util"

    def doit(self, image):
        images = [image[i:i + 1, ...] for i in range(image.shape[0])]
        return (images, )


class MakeImageList:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image1": ("IMAGE",), }}

    RETURN_TYPES = ("IMAGE",)
    OUTPUT_IS_LIST = (True,)
    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Util"

    def doit(self, **kwargs):
        images = []

        for k, v in kwargs.items():
            images.append(v)

        return (images, )


class MakeImageBatch:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image1": ("IMAGE",), }}

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Util"

    def doit(self, **kwargs):
        image1 = kwargs['image1']
        del kwargs['image1']
        images = [value for value in kwargs.values()]

        if len(images) == 0:
            return (image1,)
        else:
            for image2 in images:
                if image1.shape[1:] != image2.shape[1:]:
                    image2 = comfy.utils.common_upscale(image2.movedim(-1, 1), image1.shape[2], image1.shape[1], "lanczos", "center").movedim(1, -1)
                image1 = torch.cat((image1, image2), dim=0)
            return (image1,)


class ReencodeLatent:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                        "samples": ("LATENT", ),
                        "tile_mode": (["None", "Both", "Decode(input) only", "Encode(output) only"],),
                        "input_vae": ("VAE", ),
                        "output_vae": ("VAE", ),
                        "tile_size": ("INT", {"default": 512, "min": 320, "max": 4096, "step": 64}),
                    },
                }

    CATEGORY = "ImpactPack/Util"

    RETURN_TYPES = ("LATENT", )
    FUNCTION = "doit"

    def doit(self, samples, tile_mode, input_vae, output_vae, tile_size=512):
        if tile_mode in ["Both", "Decode(input) only"]:
            pixels = nodes.VAEDecodeTiled().decode(input_vae, samples, tile_size)[0]
        else:
            pixels = nodes.VAEDecode().decode(input_vae, samples)[0]

        if tile_mode in ["Both", "Encode(output) only"]:
            return nodes.VAEEncodeTiled().encode(output_vae, pixels, tile_size)
        else:
            return nodes.VAEEncode().encode(output_vae, pixels)


class ReencodeLatentPipe:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                        "samples": ("LATENT", ),
                        "tile_mode": (["None", "Both", "Decode(input) only", "Encode(output) only"],),
                        "input_basic_pipe": ("BASIC_PIPE", ),
                        "output_basic_pipe": ("BASIC_PIPE", ),
                    },
                }

    CATEGORY = "ImpactPack/Util"

    RETURN_TYPES = ("LATENT", )
    FUNCTION = "doit"

    def doit(self, samples, tile_mode, input_basic_pipe, output_basic_pipe):
        _, _, input_vae, _, _ = input_basic_pipe
        _, _, output_vae, _, _ = output_basic_pipe
        return ReencodeLatent().doit(samples, tile_mode, input_vae, output_vae)


class StringSelector:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "strings": ("STRING", {"multiline": True}),
            "multiline": ("BOOLEAN", {"default": False, "label_on": "enabled", "label_off": "disabled"}),
            "select": ("INT", {"min": 0, "max": sys.maxsize, "step": 1, "default": 0}),
        }}

    RETURN_TYPES = ("STRING",)
    FUNCTION = "doit"

    CATEGORY = "ImpactPack/Util"

    def doit(self, strings, multiline, select):
        lines = strings.split('\n')

        if multiline:
            result = []
            current_string = ""

            for line in lines:
                if line.startswith("#"):
                    if current_string:
                        result.append(current_string.strip())
                        current_string = ""
                current_string += line + "\n"

            if current_string:
                result.append(current_string.strip())

            if len(result) == 0:
                selected = strings
            else:
                selected = result[select % len(result)]

            if selected.startswith('#'):
                selected = selected[1:]
        else:
            if len(lines) == 0:
                selected = strings
            else:
                selected = lines[select % len(lines)]

        return (selected, )
