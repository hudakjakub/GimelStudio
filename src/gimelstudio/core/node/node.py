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

import os.path
import wx
from gsnodegraph import NodeBase as NodeView

import gimelstudio.constants as const
from gimelstudio.utils import ResizeKeepAspectRatio, ConvertImageToWx
from gimelstudio.core import EvalInfo, RenderImage


class Node(NodeView):
    def __init__(self, nodegraph, _id):
        NodeView.__init__(self, nodegraph, _id)
        self.nodegraph = nodegraph
        self._id = _id
        self._properties = {}
        self._parameters = {}
        self._cache = {}
        self._cache_enabled = True
        self._edited_flag = False

        self.NodeInitProps()
        self.NodeInitParams()

    def _WidgetEventHook(self, idname, value, render):
        """ Internal dispatcher method for the Property widget
        callback event hook method, `WidgetEventHook`.

        Please do not override.
        """
        self.NodeWidgetEventHook(idname, value)
        self.SetEditedFlag(True)
        if render == True:
            self.nodegraph.parent.parent.Render()

    @property
    def NodeMeta(self):
        """ Override property for node meta information. """
        meta_info = {
            "label": "...",
            "author": "N/A",
            "version": (0, 0, 1),
            "category": "DEFAULT",
            "description": "...",
        }
        return meta_info

    @property
    def GLSLRenderer(self):
        return self.nodegraph.GLSLRenderer

    def GetLabel(self):
        return self.NodeMeta["label"]

    def GetAuthor(self):
        return self.NodeMeta["author"]

    def GetVersion(self):
        return self.NodeMeta["version"]

    def GetCategory(self):
        return self.NodeMeta["category"]

    def GetDescription(self):
        return self.NodeMeta["description"]

    def IsOutputNode(self):
        return False

    def IsNodeCacheEnabled(self):
        return self._cache_enabled

    def AddProperty(self, prop):
        self._properties[prop.IdName] = prop
        return self._properties

    def AddParameter(self, param):
        self._parameters[param.IdName] = param
        return self._parameters

    def EditProperty(self, idname, value, render=True):
        prop = self._properties[idname]
        prop.SetValue(value, render)
        return prop

    def EditParameter(self, idname, value):
        param = self._parameters[idname]
        param.SetBinding(value)
        self.RemoveFromCache(idname)
        return param

    def SetEditedFlag(self, edited=True):
        self._edited_flag = edited

    def GetEditedFlag(self):
        return self._edited_flag

    def NodeInitProps(self):
        """ Define node properties for the node. These will translate into widgets for editing the property in the Node Properties Panel if the Property is not hidden with ``visible=False``.

        Subclasses of the ``Property`` object such as ``LabelProp``, etc. are to be added with the ``NodeAddProp`` method.

        >>> self.lbl_prop = api.LabelProp(idname="Example", default="", label="Example label:", visible=True)
        >>> self.NodeAddProp(self.lbl_prop)
        """
        pass

    def NodeInitParams(self):
        """ Define node parameters for the node. These will translate into node sockets on the node itself.

        Subclasses of the ``Parameter`` object such as ``RenderImageParam`` are to be added with the ``NodeAddParam`` method.

        >>> p = api.RenderImageParam('Image')
        >>> self.NodeAddParam(p)
        """
        pass

    def NodeAddProp(self, prop):
        """ Add a property to this node.

        :param prop: instance of `PropertyField` property class
        :returns: dictionary of the current properties
        """
        prop.SetWidgetEventHook(self._WidgetEventHook)
        return self.AddProperty(prop)

    def NodeAddParam(self, param):
        """ Add a parameter to this node.

        :param prop: instance of ``Parameter`` parameter class
        :returns: dictionary of the current parameter
        """
        return self.AddParameter(param)

    def NodeEditProp(self, idname, value, render=True):
        """ Edit a property of this node.

        :param name: name of the property
        :param value: new value of the property
        :param render: if set to ``False``, the node graph will not render after the property is edited as it usually would
        :returns: the current property value
        """
        return self.EditProperty(idname, value, render)

    def NodePanelUI(self, parent, sizer):
        """ Create the Node property widgets for the Node Property Panel. Please do not override unless you know what you're doing.
        """
        for prop in self._properties:
            prop_obj = self._properties[prop]
            if prop_obj.GetIsVisible() is True:
                prop_obj.CreateUI(parent, sizer)

    def NodeUpdateThumb(self, image):
        if self.IsExpanded():
            image = image.Image("numpy")
            img = ResizeKeepAspectRatio(image, (134, image.shape[1]))
            self.SetThumbnail(ConvertImageToWx(img))
            self.nodegraph.UpdateNodeGraph()

    def NodeEvalSelf(self):
        return self.NodeEvaluation(EvalInfo(self))

    def NodeEvaluation(self, eval_info):
        return None

    def NodeWidgetEventHook(self, idname, value):
        """ Property widget callback event hook. This method is called after the property widget has returned the new value. It is useful for updating the node itself or other node properties as a result of a change in the value of the property.

        **Keep in mind that this is only called after a property is edited by the user. If you are looking for more flexibility, you should look into creating your own Property.**

        :prop idname: idname of the property which was updated and is calling this method
        :prop value: updated value of the property
        """
        pass

    def NodeDndEventHook(self):
        pass

    def ClearCache(self):
        self._cache = {}

    def RemoveFromCache(self, name):
        cached = self.IsInCache(name)
        if cached is True and self.IsNodeCacheEnabled() is True:
            del self._cache[name]

    def IsInCache(self, name):
        try:
            self._cache[name]
            return True
        except KeyError:
            return False

    def EvalParameter(self, eval_info, name):
        cached = self.IsInCache(name)

        # Basic node cache implementation
        if self.IsNodeCacheEnabled() == True:
            if self.GetEditedFlag() == True and cached == True:
                value = self._cache[name]
                self.SetEditedFlag(False)
                # print("Used Cache: ", self._label)
            else:
                value = eval_info.EvaluateParameter(name)
                self._cache[name] = value
                self.SetEditedFlag(False)
                # print("Evaluated: ", self._label)
        else:
            value = eval_info.EvaluateParameter(name)

        return value

    def EvalProperty(self, eval_info, name):
        return eval_info.EvaluateProperty(name)

    @property
    def EvaluateNode(self):
        """ Internal method. Please do not override. """
        if self.IsMuted():
            return self.MutedNodeEvaluation
        return self.NodeEvaluation

    def EvalMutedNode(self, eval_info):
        try:
            image = self.EvalParameter(eval_info, "image").Image("numpy")
        except:
            image = self.EvalParameter(eval_info, "image 1").Image("numpy")
        render_image = RenderImage()
        render_image.SetAsImage(image)
        self.NodeUpdateThumb(render_image)
        return render_image

    def RenderGLSL(self, path, props, image, image2=None):
        file_path = os.path.expanduser(os.path.expandvars(path))
        shader_path = os.path.join(const.APP_DIR, file_path)
        shader = self.GLSLRenderer.LoadGLSLFile(shader_path)
        self.GLSLRenderer.Render(shader, props, image, image2)
        return self.GLSLRenderer.ReadNumpy()

    def RefreshNodeGraph(self):
        """ Force a refresh of the Node Graph panel. """
        self.nodegraph.UpdateNodeGraph()

    def RefreshPropertyPanel(self):
        """ Force a refresh of the Node Properties panel. """
        wx.CallAfter(self.nodegraph.parent.prop_pnl.UpdatePanelContents, self)
