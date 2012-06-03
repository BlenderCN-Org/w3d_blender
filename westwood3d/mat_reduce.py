import copy
    
def mat_reduce(root, ignore_lightmap):
    materials = []
    mathash = {}
    
    for mesh in root.find('mesh'):
        verts = mesh.get('vertices').vertices
        faces = mesh.get('triangles').triangles
        mpass = mesh.findRec('material_pass')
        texnames = mesh.findRec('texture_name')
        vmnames = mesh.findRec('vertex_material_name')
        vminfos = mesh.findRec('vertex_material_info')
        
        fmhash = {}
        mesh.Materials = []
        faceidx = 0
        for face in faces:
            
            # Gather face information
            finfo = {}
            
            # get surface
            finfo['surface'] = face['Attributes']
            
            finfo['mpass'] = []
            for p in mpass:
                pinfo = { 'stages': [] }
                
                # get vertex material
                ids = p.get('vertex_material_ids').ids
                pinfo['vmid'] = ids[face['Vindex'][0]] if len(ids) > 1 else ids[0]
                
                # remove lightmaps if not wanted
                if ignore_lightmap and vmnames[pinfo['vmid']].name == 'Lightmap':
                    mpass.remove(p)
                    continue
                
                # get shader
                ids = p.get('shader_ids').ids
                pinfo['sid'] = ids[faceidx] if len(ids) > 1 else ids[0]
                
                # get textures
                stage = p.get('texture_stage')
                if stage is not None:
                    for tex in stage.findRec('texture_ids'):
                        ids = tex.ids
                        pinfo['stages'].append(ids[faceidx] if len(ids) > 1 else ids[0])
                
                finfo['mpass'].append(pinfo)
            
            faceidx += 1
            
            # Reduce face info to materials
            h = make_hash(finfo)
            if h in fmhash:
                face['Mindex'] = fmhash[h]
                continue
            
            # Material are stored in an array with the mesh
            # and material index is stored with face
            face['Mindex'] = len(mesh.Materials)
            fmhash[h] = len(mesh.Materials)
            
            # Compile material
            mat = { 'mpass': [] }
            mat['surface'] = finfo['surface']
            
            for pinfo in finfo['mpass']:
                p = { 'vertex_material': {}, 'stages': [] }
                p['vertex_material']['name'] = vmnames[pinfo['vmid']].name
                p['vertex_material']['info'] = vminfos[pinfo['vmid']]
                for id in pinfo['stages']:
                    if id < len(texnames):
                        p['stages'].append({ 'name': texnames[id].name })
                mat['mpass'].append(p)
            
            # Reduce materials to share between meshes
            h = make_hash(mat)
            if h in mathash:
                mat = mathash[h]
            else:
                mathash[h] = mat
                materials.append(mat)
            
            mesh.Materials.append(mat)
    
    return materials
    
# thanks jomido @ stackoverflow!
DictProxyType = type(object.__dict__)

def make_hash(o):

    """
    Makes a hash from a dictionary, list, tuple or set to any level, that 
    contains only other hashable types (including any lists, tuples, sets, and
    dictionaries). In the case where other kinds of objects (like classes) need 
    to be hashed, pass in a collection of object attributes that are pertinent. 
    For example, a class can be hashed in this fashion:

        make_hash([cls.__dict__, cls.__name__])

    A function can be hashed like so:

        make_hash([fn.__dict__, fn.__code__])
    """

    if type(o) == DictProxyType:
        o2 = {}
        for k, v in o.items():
            if not k.startswith("__"):
                o2[k] = v
        o = o2    

    if isinstance(o, set) or isinstance(o, tuple) or isinstance(o, list):

        return tuple([make_hash(e) for e in o])        

    elif not isinstance(o, dict):

        return hash(o)

    new_o = copy.deepcopy(o)
    for k, v in new_o.items():
        new_o[k] = make_hash(v)

    return hash(tuple(frozenset(new_o.items())))