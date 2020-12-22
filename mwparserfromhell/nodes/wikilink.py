# Copyright (C) 2012-2020 Ben Kurtovic <ben.kurtovic@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from ._base import Node
from ..utils import parse_anything

__all__ = ["Wikilink"]

TECHNICAL = set(
"en ceb sv de fr nl ru it es pl war vi ja zh pt ar uk fa sr ca no id ko fi hu sh cs ro eu tr ms eo hy bg ce da he sk zh-min-nan kk min hr et lt be el sl gl azb az nn simple ur th hi ka uz la ta vo cy mk ast tg lv mg tt oc af bs ky sq tl bn zh-yue new te be-tarask br ml pms su nds lb jv ht mr sco szl sw ga ba pnb is my fy cv lmo an ne yo pa bar io gu als ku scn kn bpy ckb wuu ia arz qu mn bat-smg si wa cdo or yi am gd nap bug ilo mai hsb map-bms fo xmf mzn li vec sd eml sah os diq sa ps mrj mhr zh-classical hif nv roa-tara bcl ace hak frr pam nso km se rue mi vls nah bh nds-nl crh gan vep sc ab as bo glk myv co so tk fiu-vro lrc csb kv gv sn udm zea ay ie pcd nrm kab ug stq lez ha kw mwl gom haw gn rm lij lfn lad lo koi mt frp fur dsb dty ext ang ln olo cbk-zam dv bjn ksh gag pi pfl pag av bxr gor xal krc za pap kaa pdc tyv rw to kl nov jam arc kbp kbd tpi tet ig sat ki zu wo na jbo roa-rup lbe bi ty mdf kg lg tcy srn inh xh atj ltg chr sm pih om ak tn cu ts tw rmy bm st chy rn got tum ny ss ch pnt fj iu ady ve ee ks ik sg ff dz ti din cr ng cho kj mh ho ii aa mus hz kr shn hyw".split() + ["category", "file"])

NOT_CAPTION = [
    "thumb", "frame", "border", "right", "left", "center", "none",
    "baseline", "middle", "sub", "super", "text-top", "text-bottom", "top", "bottom",
    "upright"
] 

class Wikilink(Node):
    """Represents an internal wikilink, like ``[[Foo|Bar]]``."""

    def __init__(self, title, text=None):
        super().__init__()
        self.title = title
        self.text = text

    def __str__(self):
        if self.text is not None:
            return "[[" + str(self.title) + "|" + str(self.text) + "]]"
        return "[[" + str(self.title) + "]]"

    def __children__(self):
        yield self.title
        if self.text is not None:
            yield self.text

    def __strip__(self, **kwargs):
        special_link_name = self.title.partition(":")[0].lower().strip()
        if special_link_name in TECHNICAL:
            return ""
        if special_link_name == "image" and self.text:
            caption_parts = []
            for entry in self.text.split("|"):
                if entry[-2:] == "px":
                    continue
                if any(entry.startswith(prefix) for prefix in NOT_CAPTION):
                    continue
                caption_parts.append(entry)
            caption = "|".join(caption_parts)
            return parse_anything(caption).strip_code(**kwargs)

        if self.text is not None:
            return self.text.strip_code(**kwargs)
        return self.title.strip_code(**kwargs)

    def __showtree__(self, write, get, mark):
        write("[[")
        get(self.title)
        if self.text is not None:
            write("    | ")
            mark()
            get(self.text)
        write("]]")

    @property
    def title(self):
        """The title of the linked page, as a :class:`.Wikicode` object."""
        return self._title

    @property
    def text(self):
        """The text to display (if any), as a :class:`.Wikicode` object."""
        return self._text

    @title.setter
    def title(self, value):
        self._title = parse_anything(value)

    @text.setter
    def text(self, value):
        if value is None:
            self._text = None
        else:
            self._text = parse_anything(value)
