
from ..utils import make_counter
from ..structure.base import SaccharideCollection, SaccharideBase
from ..structure import Substituent
from ..structure import Monosaccharide
from ..structure import Modification
from ..structure import Glycan
from ..algorithms.similarity import commutative_similarity

from .composition import Composition


def derivatize(saccharide, substituent):
    '''
    For each monosaccharide and viable substituent, attach the specified
    substituent.

    .. warning::
        This function mutates the input `saccharide` object, because copying objects
        is expensive. If you want to continue using the underivatized object, create
        a copy of it using the object's :meth:`.clone` method.

    See Also
    --------
    :func:`.strip_derivitization`

    '''
    if isinstance(substituent, basestring):
        substituent = Substituent(substituent)
    id_base = make_counter(-substituent.id * 32)
    if isinstance(saccharide, SaccharideCollection):
        for node in saccharide:
            _strip_derivatization_monosaccharide(node)
            _derivatize_monosaccharide(node, substituent, id_base)
        saccharide._derivatized(substituent, id_base)
    elif isinstance(saccharide, SaccharideBase):
        _derivatize_monosaccharide(saccharide, substituent, id_base)
    return saccharide


def _derivatize_monosaccharide(monosaccharide_obj, substituent, id_base=None):
    '''
    The internal worker for :func:`derivatize`. It should not be called directly.

    Adds a copy of `substituent` to every open position on `monosaccharide_obj` and
    its substituents and reducing end

    Parameters
    ----------
    monosaccharide_obj: Monosaccharide
    substituent: Substituent
    id_base: function or None

    Returns
    -------
    monosaccharide_obj
    '''
    if id_base is None:
        id_base = make_counter(-substituent.id * 32)
    attachment_composition_loss = substituent.attachment_composition_loss()
    open_sites, unknowns = monosaccharide_obj.open_attachment_sites()
    for site in open_sites[unknowns:]:
        s = substituent.clone()
        s.id = id_base()
        s._derivatize = True
        monosaccharide_obj.add_substituent(
            s, parent_loss=attachment_composition_loss,
            position=site, child_loss=Composition(H=1), child_position=1)
    for p, subst in monosaccharide_obj.substituents():
        if subst.is_nh_derivatizable and substituent.can_nh_derivatize:
            s = substituent.clone()
            s._derivatize = True
            s.id = id_base()
            subst.add_substituent(s, position=2, child_position=1)
    red_end = monosaccharide_obj.reducing_end
    if red_end is not None:
        _derivatize_reducing_end(red_end, substituent, id_base)

    for pos, mod in monosaccharide_obj.modifications.items():
        if mod == Modification.a:
            s = substituent.clone()
            s._derivatize = True
            s.id = id_base()
            monosaccharide_obj.add_substituent(
                s, position=pos, parent_loss=attachment_composition_loss, max_occupancy=3,
                child_loss=Composition(H=1), child_position=1)


def _derivatize_reducing_end(reducing_end, substituent, id_base=None):
    attachment_composition_loss = substituent.attachment_composition_loss()
    for i in range(1, reducing_end.valence + 1):
        s = substituent.clone()
        s._derivatize = True
        s.id = id_base()
        reducing_end.add_substituent(
            s, parent_loss=attachment_composition_loss, max_occupancy=3,
            position=i, child_loss=Composition(H=1), child_position=1)


def strip_derivatization(saccharide):
    '''
    For each monosaccharide and viable substituent, remove all substituents
    added by :func:`derivatize`.

    .. warning::
        This function, like :func:`derivatize`, will mutate the input `saccharide`.

    See Also
    --------
    :func:`.derivatize`
    '''
    if isinstance(saccharide, SaccharideCollection):
        map(_strip_derivatization_monosaccharide, saccharide)
        saccharide._strip_derivatization()
    else:
        _strip_derivatization_monosaccharide(saccharide)
    return saccharide


def _strip_derivatization_monosaccharide(monosaccharide_obj):
    for pos, subst_link in monosaccharide_obj.substituent_links.items():
        if subst_link.child._derivatize:
            monosaccharide_obj.drop_substituent(pos, subst_link.child)
        else:
            sub_node = subst_link.child
            for sub_pos, subst_link in sub_node.links.items():
                try:
                    if subst_link.child._derivatize:
                        sub_node.drop_substituent(sub_pos, subst_link.child)
                except AttributeError:
                    if subst_link.child.node_type is Monosaccharide.node_type:
                        _strip_derivatization_monosaccharide(subst_link.child)
    red_end = monosaccharide_obj.reducing_end
    if red_end is not None:
        _strip_derivatization_reducing_end(red_end)


def _strip_derivatization_reducing_end(reducing_end):
    for pos, subst_link in reducing_end.links.items():
        if subst_link.child._derivatize:
            reducing_end.drop_substituent(pos, subst_link.child)


def has_derivatization(residue):
    for pos, link in tuple(residue.substituent_links.items()):
        if link.child._derivatize:
            return link.child
    return False


# WIP
class DerivatizeBase(object):  # pragma: no cover
    def __init__(self, substituent, white_list, black_list, *args, **kwargs):
        self.substituent = substituent
        self.white_list = white_list
        self.black_list = black_list

    def on_reducing_end(self, node):
        pass

    def on_terminal(self, node):
        pass

    def on_substituent(self, node):
        pass
