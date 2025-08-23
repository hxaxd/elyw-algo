from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from config.constant import CommonConstant
from exceptions.exception import ServiceException
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_algo.file.dao.file_dao import FileDao
from module_algo.file.entity.vo.file_vo import DeleteFileModel, FileModel, FilePageQueryModel
from utils.common_util import CamelCaseUtil
from utils.excel_util import ExcelUtil
from fastapi import UploadFile

import uuid
from pathlib import Path
import os
from datetime import datetime

class FileService:
    """
    文件模块服务层
    """

    @classmethod
    async def get_file_list_services(
        cls, query_db: AsyncSession, query_object: FilePageQueryModel, is_page: bool = False):
        """
        获取文件列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 文件列表信息对象
        """
        file_list_result = await FileDao.get_file_list(query_db, query_object, is_page)

        return file_list_result


    @classmethod
    async def add_file_services(cls, query_db: AsyncSession, page_object: FileModel, file: UploadFile):
        """
        新增文件信息service

        :param query_db: orm对象
        :param page_object: 新增文件对象
        :return: 新增文件校验结果
        """
        try:

            upload_dir = Path(f"upload_file")
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_name = page_object.name
            file_path = ""
            file_size = None
            file_type = page_object.type

            if file_type != "dir":
                file_extension = os.path.splitext(file.filename)[1]
                if file_type is None:
                    file_type = file_extension

                # 生成随机文件名
                random_filename = f"{uuid.uuid4()}{file_extension}"

                if file_name is None:
                    file_name = file.filename

                # 保存文件到指定目录
                file_path = upload_dir / random_filename
                with open(file_path, "wb") as f:
                    f.write(await file.read())
                file_size = file.size
            page_object.name = file_name
            page_object.path = str(file_path)
            page_object.size = file_size
            page_object.upload_time = datetime.now()
            page_object.type = file_type
            
            await FileDao.add_file_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_file_services(cls, query_db: AsyncSession, page_object: FileModel):
        """
        编辑文件信息service

        :param query_db: orm对象
        :param page_object: 编辑文件对象
        :return: 编辑文件校验结果
        """
        edit_file = page_object.model_dump(exclude_unset=True, exclude={'id', 'size', 'upload_time', 'dept', 'path'})
        file_info = await FileDao.get_file_detail_by_id(query_db, id=page_object.id)
        if file_info.id:
            try:
                await FileDao.edit_file_dao(query_db, edit_file)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='文件不存在')

    @classmethod
    async def delete_file_services(cls, query_db: AsyncSession, page_object: DeleteFileModel):
        """
        删除文件信息service

        :param query_db: orm对象
        :param page_object: 删除文件对象
        :return: 删除文件校验结果
        """
        if page_object.ids:
            id_list = page_object.ids.split(',')
            try:
                for id in id_list:
                    id = int(id)
                    file_info = await FileDao.get_file_detail_by_id(query_db, id=id)
                    if file_info.type == "dir":
                        file_list = await FileDao.get_file_detail_by_root(query_db, id)
                        if file_list:
                            raise ServiceException(message='文件夹下存在文件，不能删除')
                    else:
                        file_path = Path(file_info.path)
                        if file_path.exists():
                            os.remove(file_path)
                        else:
                            raise ServiceException(message='文件不存在')
                    await FileDao.delete_file_dao(query_db, FileModel(id=id))
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入文件唯一标识为空')

    @classmethod
    async def file_detail_services(cls, query_db: AsyncSession, id: int, dept_id: int):
        """
        获取文件详细信息service

        :param query_db: orm对象
        :param id: 文件唯一标识
        :return: 文件唯一标识对应的信息
        """
        result = None
        file = await FileDao.get_file_detail_by_id(query_db, id=id)
        if file.dept != dept_id:
            return None
        if file:
            if file.type == "dir":
                import zipfile
                import io
                import os
                from pathlib import Path
                zip_buffer = io.BytesIO()
                stack = [(file.id, "")]
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    while stack:
                        current_id, current_rel_path = stack.pop()
                        current_file = await FileDao.get_file_detail_by_id(query_db,current_id)

                        if current_file.type == "dir":
                            # 获取该目录下的所有文件和子目录
                            children = await FileDao.get_file_detail_by_root(query_db,current_id) # 修改为使用 id

                            for child in children:
                                # 构建子项的相对路径
                                child_rel_path = os.path.join(current_rel_path, child.name)

                                if child.type == "dir":
                                    # 如果是目录，压入栈中继续处理
                                    stack.append((child.id, child_rel_path))
                                else:
                                    # 如果是文件，添加到zip中
                                    try:
                                        file_path = Path(child.path)
                                        if file_path.exists():
                                            # 在zip中创建目录结构
                                            arcname = child_rel_path.replace(os.sep, '/')
                                            zip_file.write(file_path, arcname)
                                    except Exception as e:
                                        print(f"压缩文件时错误: {str(e)}")
                                        continue
                        else:
                            # 处理文件（理论上不应该进入这里，因为栈中只压入目录）
                            try:
                                file_path = Path(current_file.filepath)
                                if file_path.exists():
                                    arcname = current_rel_path.replace(os.sep, '/')
                                    zip_file.write(file_path, arcname)
                            except Exception as e:
                                continue
                zip_buffer.seek(0)
                dirname = file.name.encode("utf8")
                filename = f"{dirname}.zip"
                from fastapi.responses import StreamingResponse
                return StreamingResponse(
                    content=zip_buffer,
                    media_type="application/zip",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}",
                        "Content-Length": str(zip_buffer.getbuffer().nbytes)
                    }
                )
            else:
                from pathlib import Path
                from fastapi.responses import FileResponse
                path = Path(file.path)
                if not path.exists():
                    raise ServiceException(message=f'文件路径{path}不存在')
                result = FileResponse(path=path, filename=file.name)
        else:
            result = None

        return result

    @classmethod
    async def unzip_file_services(cls, query_db: AsyncSession, id: int, dept_id: int):
        """
        解压文件service

        :param query_db: orm对象
        :param id: 文件唯一标识
        :return: 解压文件校验结果
        """
        try:
            file = await FileDao.get_file_detail_by_id(query_db, id)
            if file is None:
                raise ServiceException(message='文件不存在')
            if file.type != 'zip':
                raise ServiceException(message='只能解压zip文件')
            if file.dept != dept_id:
                raise ServiceException(message='您没有权限解压该文件')
            name = file.name.replace(".zip", "")
            zip_path = Path(file.path)
            result_dir = zip_path.parent / uuid.uuid4().hex
            result_dir.mkdir(parents=True, exist_ok=True)
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(result_dir)

                dir_path = result_dir

                # 创建目录记录
                dir_record = FileModel(
                    name=name,
                    root=file.root,
                    type="dir",
                    upload_time=datetime.now(),
                    dept = dept_id,
                )
                query_db.add(dir_record)
                await query_db.commit()
                await query_db.refresh(dir_record)

                def get_file_type(filepath: Path) -> str:
                    if filepath.is_dir():
                        return "dir"
                    suffix = filepath.suffix
                    if suffix:
                        return suffix[1:].lower()
                    if os.access(filepath, os.X_OK):
                        return "executable"
                    return "unknown"

                # 创建文件记录（如果需要记录单个文件）
                for file_path in dir_path.rglob('*'):
                    file_record = FileModel(
                        name=file_path.name,
                        path=str(file_path),
                        root=dir_record.id,
                        type=get_file_type(file_path),
                        upload_time=datetime.now(),
                        dept = dept_id,
                        size=file_path.stat().st_size if file_path.is_file() else 0,
                    )
                    query_db.add(file_record)
                await query_db.commit()

            return CrudResponseModel(is_success=True, message='解压成功')

        except Exception as e:
            await query_db.rollback()
            raise e