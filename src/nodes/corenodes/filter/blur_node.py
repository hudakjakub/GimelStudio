# ----------------------------------------------------------------------------
# Gimel Studio Copyright 2019-2021 by Noah Rahm and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------

import cv2

from gimelstudio import api


class BlurNode(api.Node):
    def __init__(self, nodegraph, _id):
        api.Node.__init__(self, nodegraph, _id)

    @property
    def NodeMeta(self):
        meta_info = {
            "label": "Blur",
            "author": "Gimel Studio",
            "version": (2, 5, 0),
            "category": "FILTER",
            "description": "Blurs the given image using the specified blur type and kernel.",
        }
        return meta_info

    def NodeInitProps(self):
        self.filter_type = api.ChoiceProp(
            idname="filter_type",
            default="Box",
            choices=["Box", "Gaussian"],
            fpb_label="Filter Type"
        )
        self.kernel_x = api.PositiveIntegerProp(
            idname="kernel_x",
            default=5,
            min_val=1,
            max_val=500,
            fpb_label="Kernel X",
        )
        self.kernel_y = api.PositiveIntegerProp(
            idname="kernel_y",
            default=5,
            min_val=1,
            max_val=500,
            fpb_label="Kernel Y",
        )
        self.NodeAddProp(self.filter_type)
        self.NodeAddProp(self.kernel_x)
        self.NodeAddProp(self.kernel_y)

    def NodeInitParams(self):
        image = api.RenderImageParam("image", "Image")

        self.NodeAddParam(image)

    def MutedNodeEvaluation(self, eval_info):
        return self.EvalMutedNode(eval_info)

    def NodeEvaluation(self, eval_info):
        kernel_x = self.EvalProperty(eval_info, "kernel_x")
        kernel_y = self.EvalProperty(eval_info, "kernel_y")
        filter_type = self.EvalProperty(eval_info, "filter_type")
        image1 = self.EvalParameter(eval_info, "image")

        render_image = api.RenderImage()
        img = image1.Image("numpy")

        if filter_type == "Box":
            output_img = cv2.boxFilter(img, -1, (kernel_x, kernel_y))
        elif filter_type == "Gaussian":
            # Both values must be odd
            if (kernel_x % 2) == 0 and (kernel_y % 2) == 0:
                kernel_y += 1
                kernel_x += 1

            output_img = cv2.GaussianBlur(img, (0, 0), sigmaX=kernel_x, sigmaY=kernel_y)

        render_image.SetAsImage(output_img)
        self.NodeUpdateThumb(render_image)
        return render_image


api.RegisterNode(BlurNode, "corenode_blur")
