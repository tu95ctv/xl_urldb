# -*- coding: utf-8 -*-
# import xlwt
# from dltool import generate_easyxf as generate_easyxf_import
# from dltool import  write_table_rerange, common_one_table_report_xl, font_decorator_parent_new
# from dltool import display_from_to

# -*- coding: utf-8 -*-
import requests
from collections import  OrderedDict
from time import sleep
import xlwt
from datetime import datetime
import re
def font_decorator_parent_new(**kkgargs):
    def font_decorator(func):
        def awrapper(*args, **kargs):
            for k,v  in kkgargs.items():
                if k not in kargs and v:
                    kargs[k] = v
            rs = func(*args, **kargs)
            return rs
        return awrapper
    return font_decorator
def generate_easyxf_import (font='Times New Roman', 
                     bold = False,
                     underline=False,
                     height=12, 
                     align_wrap = False,
                     vert = False,
                     horiz = False,
                     borders = False,
                     pattern = False,
                     italic= False,**kargs
                     ):
    fonts = []
    fonts.append('name %s'%font)
    if underline:
        fonts.append('underline on')
    if bold:
        fonts.append('bold on')
        
    if italic:
        fonts.append('italic on')
        
    fonts.append('height %s'%(height*20))
    sums = []
    font = 'font: ' + ','.join(fonts)
    sums.append(font)
    
    aligns = []
    if vert:
        aligns.append('vert %s'%vert)
    if horiz:
        aligns.append('horiz %s'%horiz)
    if align_wrap:
        aligns.append('wrap on')
        
    if aligns:
        align = 'align:  ' + ','.join(aligns)
#         font = font + '; ' + align
        sums.append(align)
    
  
    if borders:
        borders = 'borders: ' + borders
        sums.append(borders) 
    
    if pattern:
        pattern = 'pattern: ' + pattern
        sums.append(pattern)
#     for k,v in kargs.items():
#         sums.append(k+': ' + v)
    sums = ';'.join(sums)   
    return sums


def get_hasura_data(data):
    url = 'https://qlth.hpz.vn/v1/graphql'
    headers = {'x-hasura-admin-secret': 'hpz', 'content-type': 'application/json', 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'}
    count_fail = 0
    while 1:
        print ('get html',url)
        try:
            request = requests.post(url, json=data, headers=headers)
            return request.json()
        except Exception as e:
            count_fail +=1
            print ('loi khi get html',e)
            sleep(5)
            if count_fail ==5:
                raise ValueError(u'Lỗi get html')


def write_fixups(fixups_setting):
    fixups = fixups_setting['fixups']
    defaut_fixups_style = fixups_setting['default_fixups_style']
    wb = xlwt.Workbook()
    sheet_name = fixups_setting.get('sheet_name','Sheet 1')
    ws = wb.add_sheet(sheet_name, cell_overwrite_ok=True)
    irow = 0
    fixups = OrderedDict (fixups)
    height = fixups_setting.get('row_height')
    for k_fixups, v_fixups in fixups.items():
        skip_row = v_fixups.get('skip_row')
        if skip_row:
            continue
        break_sheet = v_fixups.get('break_sheet')
        if break_sheet:
            sheet_name = v_fixups.get('sheet_name','Sheet 1')
            ws = wb.add_sheet(sheet_name, cell_overwrite_ok=True)
            irow = 0
        row_height = v_fixups.get('row_height')
        height = row_height or height
        xrange = v_fixups['range']
        if xrange[0] == 'auto':
            offset = v_fixups.get('offset', 1 )
            irow = irow + offset
            xrange[0] = irow
            if len(xrange) == 4:
                irow = irow + xrange[1]
                xrange[1] = irow
        else:
            irow = xrange[0] 
        func = v_fixups.get('func')
        if func:
            begin_icol = xrange[1]
            func_kargs = v_fixups.get('func_kargs',{})
            func_row = func(ws, irow, begin_icol,**func_kargs)
            if func_row:
                irow = irow + func_row -1
        else:
            val = v_fixups.get('val',None)
            val_func = v_fixups.get('val_func')
            if val_func:
                val_func_kargs = v_fixups.get('val_func_kargs',{})
                val = val_func(**val_func_kargs)
                
            style = v_fixups.get('style',defaut_fixups_style)
            if len(xrange) == 2:
                ws.write(xrange[0], xrange[1], val, style)
            else:
                ws.write_merge(xrange[0], xrange[1],xrange[2], xrange[3], val, style)
                
            if height != None:
                ws.row(irow).height_mismatch = True
                ws.row(irow).height = height
    return wb
 
def get_hasura_data_with_query_and_variable(variable_values=None, query=None):
    data = {'query': query}
    if variable_values:
        data['variables'] = variable_values
    rs = get_hasura_data(data)
    return  rs
# def write_table(table_setting, datas, begin_title_irow,  begin_icol, ws,gen_row_data = None ):
def write_table_rerange(ws, begin_title_irow, begin_icol, table_setting=None):
    title_height = table_setting.get('title_height')
    datas = table_setting['datas']
    def get_width(num_characters,font_height=12):
        return int((1+num_characters) * 256*font_height/12)
    height = table_setting.get('row_height')
    default_cell_font = table_setting['default_cell_font']
    skip_width = table_setting.get('skip_width')
    def write_a_row(obj_data, FIELDNAME_FIELDATTR,  ws, irow, begin_icol,cell_font=default_cell_font):
        
        ifield = 0 
        for fname, field_attr_dict  in FIELDNAME_FIELDATTR.items():
            icol = begin_icol + ifield
            style = field_attr_dict.get('style',cell_font)
            val = obj_data.get(fname,None)
            val_func = field_attr_dict.get('val_func',None)
            if val_func:
                val = val_func(val,obj_data,FIELDNAME_FIELDATTR)
            field_attr_dict['val'] = val
            is_temp_field = field_attr_dict.get('is_temp_field',False)
            if is_temp_field:
                continue
            ws.write(irow, icol,val, style)
            if height != None:
                ws.row(irow).height_mismatch = True
                ws.row(irow).height = height
            ifield +=1
    default_merge_title_font = table_setting['default_merge_title_font']
    default_title_font = table_setting['default_title_font']
    def write_a_title(FIELDNAME_FIELDATTR, ws, irow, begin_icol, default_width, is_merge_title,merge_title_font=default_merge_title_font,title_font=default_title_font ):
        ifield = 0 
        if is_merge_title:
            merge_title_irow = irow
            title_irow = irow + 1
            if title_height != None:
                ws.row(merge_title_irow).height_mismatch = True
                ws.row(merge_title_irow).height = title_height
        else:
            title_irow = irow
            
            
        if title_height != None:
            ws.row(title_irow).height_mismatch = True
            ws.row(title_irow).height = title_height
        merge_title_old = None
        for fname, field_attr_dict  in FIELDNAME_FIELDATTR.items():
            is_temp_field = field_attr_dict.get('is_temp_field',False)
            if is_temp_field:
                continue
            icol = begin_icol + ifield
            title = field_attr_dict.get('title', fname)
            
            if is_merge_title:
                merge_title = field_attr_dict.get('merge_title', None)
                if merge_title==None or merge_title != merge_title_old:#merge_title and merge_title == merge_title_old
                    ws.write(merge_title_irow,icol,merge_title, title_font)
                    merge_title_icol_old = icol
                else:
                    ws.write_merge(merge_title_irow,merge_title_irow,merge_title_icol_old, icol, merge_title, merge_title_font )
                merge_title_old = merge_title
            if is_merge_title and  merge_title == None:
                ws.write_merge(merge_title_irow, title_irow, icol, icol, title , merge_title_font)
            else:   
                ws.write(title_irow, icol, title , title_font)
            if not skip_width:
                width = field_attr_dict.get('width',None)
                if width:
                    width = get_width(width)
                else:
                    auto_width = field_attr_dict.get('auto_width',False)
                    if auto_width:
                        width = get_width(len(title) )
                    elif default_width:
                        width = get_width(default_width)
                if width:
                    ws.col(icol).width = width
            ifield +=1
        if is_merge_title:
            return 2
        else:
            return 1
        
        
    FIELDNAME_FIELDATTR = table_setting['FIELDNAME_FIELDATTR']
    FIELDNAME_FIELDATTR = OrderedDict (FIELDNAME_FIELDATTR)
    default_width = table_setting.get('default_width',10)
    is_merge_title = table_setting.get('is_merge_title',False)  
    gen_row_data = table_setting.get('gen_row_data')
    title_nrow = write_a_title(FIELDNAME_FIELDATTR, ws, begin_title_irow, begin_icol, default_width, is_merge_title)        
    irow = begin_title_irow +title_nrow   
    for  i in datas:
        if gen_row_data:
            obj_data = gen_row_data(i)
        else:
            obj_data = i
        write_a_row(obj_data, FIELDNAME_FIELDATTR, ws, irow, begin_icol)
        irow +=1
    nrow = title_nrow + len(datas)
    return nrow
# new

def get_variable_values(request_args):
    variable_values = {}
    if 'from' in request_args:
        variable_values['from'] = request_args['from']
    if 'to' in request_args:
        variable_values['to'] = request_args['to']
    return variable_values
        
font_map = {1:'Calibri', 2:'Times New Roman'}
def get_font_font_size(request_args):
    font_font_size_dict = {}
    if 'font_size' in request_args:
        font_size = request_args['font_size']
        if font_size > 9 and font_size < 13:
            font_font_size_dict['font_size'] =  font_size
    if 'font' in request_args:
        font = request_args['font']
        if font in font_map:
            font = font_map.get(font)
            font_font_size_dict['font'] =  font
    return font_font_size_dict

def common_one_table_report_xl(request_args, basic_setting, gen_table_setting_list, gen_fixups):
    font_font_size_dict = get_font_font_size(request_args)
    font = font_font_size_dict.get('font') or  basic_setting['Font_default']
    font_size = font_font_size_dict.get('font_size') or basic_setting['Font_size_default']
   
    table_setting_list =[]
    if not isinstance(gen_table_setting_list, list):
        gen_table_setting_list = [gen_table_setting_list]
    for gen_table_setting in gen_table_setting_list:
        table_setting = gen_table_setting (font, font_size, request_args)
        if table_setting.get('get_hasura_data',True):
            get_variable_values_func = table_setting.get('get_variable_values', get_variable_values)
            variable_values = get_variable_values_func(request_args)
            data_hasura =  get_hasura_data_with_query_and_variable( variable_values=variable_values, query= table_setting['query'])
        print ('***data_hasura', data_hasura)
        raise ValueError('akaka')
        out_datas_func=table_setting.get('out_datas_func')
        if out_datas_func:
            datas =out_datas_func(data_hasura)
        else:
            datas = data_hasura
        table_setting['datas'] = datas
#         print ('datas', datas)
        table_setting_list.append(table_setting)
    if len(table_setting_list)==1:
        table_setting_list = table_setting_list[0]
    setting_fixups = gen_fixups(font, font_size,variable_values, table_setting_list, request_args)
    wb = write_fixups(setting_fixups )
    return wb

#usually func
def convert_gmt_str_dt_to_vn_str_dt(from_):
    from_ = datetime.strptime(from_,'%Y-%m-%d')
#     from_ = from_.strftime('%d/%m/%Y')
    return  from_

def display_from_to(variable_values):
    from_ = variable_values['from']
    to_ = variable_values['to']
    if from_:
        variable_values['from'] = from_
        try:
            from_ = datetime.strptime(from_,'%Y-%m-%d')
            from_ = from_.strftime('%d/%m/%Y')
        except ValueError:
            from_ = ''
    if to_:
        variable_values['to'] = to_
        try:
            to_ = datetime.strptime(to_,'%Y-%m-%d')
            to_ = to_.strftime('%d/%m/%Y')
        except ValueError:
            to_ = ''
    return u'Từ ngày %s đến ngày %s'%(from_, to_)

def easyxf_new(str_style,**kargs):
    style = xlwt.easyxf(str_style)
    for k,v in kargs.items():
        setattr(style, k, v)
    return style
    
    

Basic_setting = {
    'Font_default':'Calibri',
    'Font_size_default':11
    }
def ne_nep_gen_table_setting (font, font_size, request_args):
    ne_nep_query = '''query($from:date!,$to:date!){
  result:edu_classes_aggregate(
    order_by: {
      class_name: asc_nulls_last
    }    
  ){
    aggregate { count }
    nodes {
      id
      key:id
      class_name
      statistics:thong_ke_vi_pham_tap_thes_aggregate(
        where:{      
          day_work:{
            _gte:$from,
            _lte:$to
          }      
        }
      ){
        aggregate{
          sum{          
            slg_loi_tap_the
            diem_tru_tap_the
            slg_loi_ca_nhan
            diem_tru_ca_nhan
            slg_loi_diem_danh
            diem_tru_diem_danh
            tong_diem_tru
          }
        }
      }
    }
  }
}''' 
    
    def ne_nep_out_datas_func (rs):
        datas =rs['data']['result']['nodes']
        return datas
    def ne_nep_gen_row_data(data_item):
        class_name  = data_item['class_name']
        obj_data = data_item['statistics']['aggregate']['sum']
        obj_data['class_name'] = class_name
        return obj_data

    @font_decorator_parent_new(font = font, height = font_size, vert = 'center',  horiz = 'center' )
    def generate_easyxf(*args, **kargs):
        return generate_easyxf_import(*args, **kargs)
    ne_nep_FIELDNAME_FIELDATTR = [
            ('stt',{'val_func': lambda v,d,s:s['stt'].get('val',0)+1,'width':4,'title':u'STT'}),
            ('class_name',{'title':u'Lớp', 'width':5}),
            ('slg_loi_tap_the',{'merge_title':u'Vi phạm tập thể','title':u'Số lỗi vi phạm'}),
            ('diem_tru_tap_the',{'merge_title':u'Vi phạm tập thể','title':u'Số điểm trừ' , 'auto_width':True}),
            ('slg_loi_ca_nhan',{ 'merge_title':u'Vi phạm nề nếp cá nhân', 'title':u'Số lỗi vi phạm'}),
            ('diem_tru_ca_nhan',{'merge_title':u'Vi phạm nề nếp cá nhân', 'title':u'Số điểm trừ', 'auto_width':True}),
            ('slg_loi_diem_danh',{'merge_title':u'Vi phạm điểm danh', 'title':u'Số lỗi vi phạm' }),
            ('diem_tru_diem_danh',{'merge_title':u'Vi phạm điểm danh', 'title':u'Số điểm trừ', 'auto_width':True}),
            ('tong_diem_tru',{'title':u'Tổng điểm trừ',  'width':7.6}),
            ]
        
    ne_nep_table_setting = {
            'query':ne_nep_query,
            'out_datas_func':ne_nep_out_datas_func,
            'gen_row_data':ne_nep_gen_row_data,
            'default_width':11,
            'default_merge_title_font':xlwt.easyxf(generate_easyxf(align_wrap=True, bold=True,vert = 'center',horiz='center',borders='left thin, right thin, top thin, bottom thin')),
            'default_title_font':xlwt.easyxf(generate_easyxf(borders='left thin, right thin, top thin, bottom thin',vert = 'center',horiz = 'center')),
            'default_cell_font':xlwt.easyxf(generate_easyxf(borders='left thin, right thin, top thin, bottom thin',vert = 'center')),
            'is_merge_title':True,
            'FIELDNAME_FIELDATTR':ne_nep_FIELDNAME_FIELDATTR,
            'row_height':20*16,
            'title_height':20*26
            }
    return ne_nep_table_setting

def ne_nep_gen_fixups(font, font_size,variable_values, ne_nep_table_setting, request_args):
    @font_decorator_parent_new(font = font, height = font_size, vert = 'center',  horiz = 'center' )
    def generate_easyxf(*args, **kargs):
        return generate_easyxf_import(*args, **kargs)
    Begin_irow = 2
    Begin_icol = 0
    
    fixups_ne_nep =[  
         ('header',{'range':[Begin_irow, Begin_irow, Begin_icol, Begin_icol+7],'val':u'BÁO CÁO NỀ NẾP VI PHẠM TỔNG HỢP', 
                    'style':xlwt.easyxf(generate_easyxf(bold=True)), 'row_height': 20*21}),
         ('header2',{'range':['auto', 0, Begin_icol, Begin_icol+7],'val_func':display_from_to, 'val_func_kargs':{'variable_values':variable_values},
                      'style':xlwt.easyxf(generate_easyxf(bold=True)),  'row_height': 20*21}),
         ('table',{'range':['auto', Begin_icol],'val':None,
               'func':write_table_rerange, 'offset':2,
               'func_kargs':{'table_setting':ne_nep_table_setting,
                                }  }),
#          ('header3',{'range':['auto',Begin_icol],'val':u'Kết thúc'}),
                     ] 
    setting_fixups = {
        'row_height':20*16, 
        'fixups':fixups_ne_nep,
        'default_fixups_style':xlwt.easyxf(generate_easyxf(vert = 'center',horiz = 'center'))
        }
    return setting_fixups


def ne_nep_report_xl(request_args):
    wb = common_one_table_report_xl(request_args, Basic_setting, [ne_nep_gen_table_setting], ne_nep_gen_fixups)
    return wb


Convert_dict = {'false':False, 'true':True, '^\d+$': lambda v:int(v), '^\d+\.(\d*)$': lambda v:float(v)}
def convert_type(request_args):
    new_kargs = {}
    for k_rq, v in request_args.items():
        if isinstance(v, str):
            for pt, repl in Convert_dict.items():
                is_match = re.search(pt, v,re.I)
                print (k_rq, pt,v,is_match)
                if is_match:
                    if callable(repl):
                        v = repl(v)
                    else:
                        v = repl
                    break
        new_kargs[k_rq]= v
    return new_kargs
dlxl_map_func = {'ne_nep':{'func':ne_nep_report_xl,'file_name':'ne_nep_tong_hop'},
#                  'diem_danh':{'func':diem_danh_report_xl,'file_name':'vi_pham_diem_danh'},
#                  'nn_chi_tiet':{'func':nn_chi_tiet_report_xl,'file_name':'nn_chi_tiet'},
                 }

def get_funcxl_and_run_funcxl_from_key(func_key, request_args):
#     print ('**request_args', request_args)
    request_args = convert_type(request_args)
#     print ('**request_args convert type', request_args)
    adict = dlxl_map_func[func_key]
    func = adict['func']
    filename = adict['file_name'] +'.xls'
    wb = func(request_args)
    print ('done gen file')
    return wb, filename
    
    
    
    

if __name__ == '__main__':
    variable_values_dd ={ "from": "2019-09-16", "to": "2019-09-16", 'font_size':11 }  
    wb = ne_nep_report_xl(variable_values_dd)
    wb.save(r'C:\Users\tu\Desktop\New folder\ne_nep_tong_hop.xls')       
    print('done')


