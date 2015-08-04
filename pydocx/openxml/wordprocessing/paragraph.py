# coding: utf-8
from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

from pydocx.models import XmlModel, XmlCollection, XmlChild
from pydocx.openxml.wordprocessing.hyperlink import Hyperlink
from pydocx.openxml.wordprocessing.paragraph_properties import ParagraphProperties  # noqa
from pydocx.openxml.wordprocessing.run import Run
from pydocx.openxml.wordprocessing.smart_tag_run import SmartTagRun
from pydocx.openxml.wordprocessing.inserted_run import InsertedRun
from pydocx.openxml.wordprocessing.deleted_run import DeletedRun
from pydocx.openxml.wordprocessing.sdt_run import SdtRun


class Paragraph(XmlModel):
    XML_TAG = 'p'

    properties = XmlChild(type=ParagraphProperties)

    children = XmlCollection(
        Run,
        Hyperlink,
        SmartTagRun,
        InsertedRun,
        DeletedRun,
        SdtRun,
    )

    def __init__(self, **kwargs):
        super(Paragraph, self).__init__(**kwargs)
        self._effective_properties = None

    @property
    def effective_properties(self):
        # TODO need to calculate effective properties like Run
        if not self._effective_properties:
            properties = self.properties
            self._effective_properties = properties
        return self._effective_properties

    def has_structured_document_parent(self):
        from pydocx.openxml.wordprocessing import SdtBlock
        structured_parent = self.nearest_ancestors(SdtBlock)
        try:
            next(structured_parent)
            return True
        except StopIteration:
            pass
        return False

    def get_style_chain_stack(self):
        if not self.properties:
            return

        parent_style = self.properties.parent_style
        if not parent_style:
            return

        # TODO the getattr is necessary because of footnotes. From the context
        # of a footnote, a paragraph's container is the footnote part, which
        # doesn't have access to the style_definitions_part
        part = getattr(self.container, 'style_definitions_part', None)
        if part:
            style_stack = part.get_style_chain_stack('paragraph', parent_style)
            for result in style_stack:
                yield result

    @property
    def heading_style(self):
        if hasattr(self, '_heading_style'):
            return getattr(self, '_heading_style')
        style_stack = self.get_style_chain_stack()
        heading_style = None
        for style in style_stack:
            if style.is_a_heading():
                heading_style = style
                break
        self.heading_style = heading_style
        return heading_style

    @heading_style.setter
    def heading_style(self, style):
        self._heading_style = style

    def get_numbering_definition(self):
        # TODO add memoization

        # TODO the getattr is necessary because of footnotes. From the context
        # of a footnote, a paragraph's container is the footnote part, which
        # doesn't have access to the numbering_definitions_part
        part = getattr(self.container, 'numbering_definitions_part', None)
        if not part:
            return
        if not self.effective_properties:
            return
        numbering_properties = self.effective_properties.numbering_properties
        if not numbering_properties:
            return
        return part.numbering.get_numbering_definition(
            num_id=numbering_properties.num_id,
        )

    def get_numbering_level(self):
        # TODO add memoization
        numbering_definition = self.get_numbering_definition()
        if not numbering_definition:
            return
        if not self.effective_properties:
            return
        numbering_properties = self.effective_properties.numbering_properties
        if not numbering_properties:
            return
        return numbering_definition.get_level(
            level_id=numbering_properties.level_id,
        )