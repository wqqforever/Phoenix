#---------------------------------------------------------------------------
# Name:        etg/treectrl.py
# Author:      Robin Dunn
#
# Created:     26-Mar-2012
# Copyright:   (c) 2012 by Total Control Software
# License:     wxWindows License
#---------------------------------------------------------------------------

import etgtools
import etgtools.tweaker_tools as tools

PACKAGE   = "wx"   
MODULE    = "_core"
NAME      = "treectrl"   # Base name of the file to generate to for this script
DOCSTRING = ""

# The classes and/or the basename of the Doxygen XML files to be processed by
# this script. 
ITEMS  = [ "wxTreeItemId",
           ##"wxTreeItemData",  We're using a MappedType instead
           "wxTreeCtrl",
           "wxTreeEvent",           
           ]    

#---------------------------------------------------------------------------

def run():
    # Parse the XML file(s) building a collection of Extractor objects
    module = etgtools.ModuleDef(PACKAGE, MODULE, NAME, DOCSTRING)
    etgtools.parseDoxyXML(module, ITEMS)
    
    #-----------------------------------------------------------------
    # Tweak the parsed meta objects in the module object as needed for
    # customizing the generated code and docstrings.
    
    
    #-------------------------------------------------------
    c = module.find('wxTreeItemId')
    assert isinstance(c, etgtools.ClassDef)
    c.addCppMethod('int', '__nonzero__', '()', """\
        return self->IsOk();
        """)

    td = etgtools.TypedefDef(name='wxTreeItemIdValue', type='void*')
    module.insertItemBefore(c, td)
    
    
    #-------------------------------------------------------
    c = module.find('wxTreeCtrl')
    tools.fixWindowClass(c)
    module.addGlobalStr('wxTreeCtrlNameStr', before=c)
    
    
    # Set all wxTreeItemData parameters to transfer ownership.  Is this still needed with MappedTypes?
    for item in c.allItems():
        if hasattr(item, 'type') and item.type == 'wxTreeItemData *' and \
           isinstance(item, etgtools.ParamDef):
                item.transfer = True

    c.addPyCode("""\
        TreeCtrl.GetItemPyData = wx.deprecated(TreeCtrl.GetItemData)
        TreeCtrl.SetItemPyData = wx.deprecated(TreeCtrl.SetItemData)
        """)

    
    # We can't use wxClassInfo
    c.find('EditLabel.textCtrlClass').ignore()
    
    # Replace GetSelections with a method that returns a Python list
    # size_t GetSelections(wxArrayTreeItemIds& selection) const;
    c.find('GetSelections').ignore()
    c.addCppMethod('PyObject*', 'GetSelections', '()',
        doc='Returns a list of currently selected items in the tree.  This function '
            'can be called only if the control has the wx.TR_MULTIPLE style.',
        body="""\
        wxPyBlock_t blocked = wxPyBeginBlockThreads();
        PyObject*           rval = PyList_New(0);
        wxArrayTreeItemIds  array;
        size_t              num, x;
        num = self->GetSelections(array);
        for (x=0; x < num; x++) {
            wxTreeItemId *tii = new wxTreeItemId(array.Item(x));
            PyObject* item = wxPyConstructObject((void*)tii, wxT("wxTreeItemId"), true);
            PyList_Append(rval, item);
            Py_DECREF(item);
        }
        wxPyEndBlockThreads(blocked);
        return rval;
        """)
    
    # Change GetBoundingRect to return the rectangle instead of modifying the parameter.
    #bool GetBoundingRect(const wxTreeItemId& item, wxRect& rect, bool textOnly = false) const;    
    c.find('GetBoundingRect').ignore()
    c.addCppMethod('PyObject*', 'GetBoundingRect', '(const wxTreeItemId& item, bool textOnly=false)',
        doc="""\
        Returns the rectangle bounding the item. If textOnly is true,
        only the rectangle around the item's label will be returned, otherwise
        the item's image is also taken into account. The return value may be None 
        if the rectangle was not successfully retrieved, such as if the item is 
        currently not visible.
        """,
        isFactory=True,
        body="""\
        wxRect rect;
        if (self->GetBoundingRect(*item, rect, textOnly)) {
            wxPyBlock_t blocked = wxPyBeginBlockThreads();
            wxRect* r = new wxRect(rect);
            PyObject* val = wxPyConstructObject((void*)r, wxT("wxRect"), true);
            wxPyEndBlockThreads(blocked);
            return val;
        }
        else
            RETURN_NONE();
        """)
    
    
    # switch the virtualness back on for those methods that need to have it.
    c.find('OnCompareItems').isVirtual = True
    
    
    # transfer imagelist ownership
    c.find('AssignImageList.imageList').transfer = True
    c.find('AssignStateImageList.imageList').transfer = True
    c.find('AssignButtonsImageList.imageList').transfer = True
    
    
    # Make the cookie values be returned, instead of setting it through the parameter
    c.find('GetFirstChild.cookie').out = True
    c.find('GetFirstChild.cookie').inOut = True


    
    #-------------------------------------------------------
    c = module.find('wxTreeEvent')
    tools.fixEventClass(c)
    
    c.addPyCode("""\
        EVT_TREE_BEGIN_DRAG        = PyEventBinder(wxEVT_COMMAND_TREE_BEGIN_DRAG       , 1)
        EVT_TREE_BEGIN_RDRAG       = PyEventBinder(wxEVT_COMMAND_TREE_BEGIN_RDRAG      , 1)
        EVT_TREE_BEGIN_LABEL_EDIT  = PyEventBinder(wxEVT_COMMAND_TREE_BEGIN_LABEL_EDIT , 1)
        EVT_TREE_END_LABEL_EDIT    = PyEventBinder(wxEVT_COMMAND_TREE_END_LABEL_EDIT   , 1)
        EVT_TREE_DELETE_ITEM       = PyEventBinder(wxEVT_COMMAND_TREE_DELETE_ITEM      , 1)
        EVT_TREE_GET_INFO          = PyEventBinder(wxEVT_COMMAND_TREE_GET_INFO         , 1)
        EVT_TREE_SET_INFO          = PyEventBinder(wxEVT_COMMAND_TREE_SET_INFO         , 1)
        EVT_TREE_ITEM_EXPANDED     = PyEventBinder(wxEVT_COMMAND_TREE_ITEM_EXPANDED    , 1)
        EVT_TREE_ITEM_EXPANDING    = PyEventBinder(wxEVT_COMMAND_TREE_ITEM_EXPANDING   , 1)
        EVT_TREE_ITEM_COLLAPSED    = PyEventBinder(wxEVT_COMMAND_TREE_ITEM_COLLAPSED   , 1)
        EVT_TREE_ITEM_COLLAPSING   = PyEventBinder(wxEVT_COMMAND_TREE_ITEM_COLLAPSING  , 1)
        EVT_TREE_SEL_CHANGED       = PyEventBinder(wxEVT_COMMAND_TREE_SEL_CHANGED      , 1)
        EVT_TREE_SEL_CHANGING      = PyEventBinder(wxEVT_COMMAND_TREE_SEL_CHANGING     , 1)
        EVT_TREE_KEY_DOWN          = PyEventBinder(wxEVT_COMMAND_TREE_KEY_DOWN         , 1)
        EVT_TREE_ITEM_ACTIVATED    = PyEventBinder(wxEVT_COMMAND_TREE_ITEM_ACTIVATED   , 1)
        EVT_TREE_ITEM_RIGHT_CLICK  = PyEventBinder(wxEVT_COMMAND_TREE_ITEM_RIGHT_CLICK , 1)
        EVT_TREE_ITEM_MIDDLE_CLICK = PyEventBinder(wxEVT_COMMAND_TREE_ITEM_MIDDLE_CLICK, 1)
        EVT_TREE_END_DRAG          = PyEventBinder(wxEVT_COMMAND_TREE_END_DRAG         , 1)
        EVT_TREE_STATE_IMAGE_CLICK = PyEventBinder(wxEVT_COMMAND_TREE_STATE_IMAGE_CLICK, 1)
        EVT_TREE_ITEM_GETTOOLTIP   = PyEventBinder(wxEVT_COMMAND_TREE_ITEM_GETTOOLTIP,   1)
        EVT_TREE_ITEM_MENU         = PyEventBinder(wxEVT_COMMAND_TREE_ITEM_MENU,         1)
        """)
    
    #-----------------------------------------------------------------
    tools.doCommonTweaks(module)
    tools.runGenerators(module)
    
    
#---------------------------------------------------------------------------
if __name__ == '__main__':
    run()

