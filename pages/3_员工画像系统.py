# -*- coding: utf-8 -*-
"""
员工画像系统 - 员工数字人管理
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from src.employees.store import EmployeeStore
from src.models.employee import EmployeeProfile, EMPLOYEE_STYLE_TYPES

st.set_page_config(page_title="员工画像系统", page_icon="👤", layout="wide")
st.title("👤 员工画像系统")

store = EmployeeStore()
employees = store.list_all()

# 展示所有员工
st.subheader("员工列表")
for emp in employees:
    with st.expander(f"**{emp.name}** | {emp.position} | {emp.ai_assistant_type}", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**岗位**:", emp.position)
            st.write("**行业经验**:", emp.industry_experience or "-")
            st.write("**内容风格**:", emp.content_style)
            st.write("**AI助手类型**:", emp.ai_assistant_type)
            st.write("**擅长领域**:", ", ".join(emp.expertise) if emp.expertise else "-")
        with col2:
            # 创意历史
            history = store.get_creative_history(emp.id, limit=5)
            st.write("**创意历史** (最近5条):")
            for h in history:
                st.caption(f"- {h.topic} | {len(h.ideas)} 个创意")
        if st.button("删除", key=f"del_{emp.id}"):
            store.delete(emp.id)
            st.rerun()

st.divider()
st.subheader("新增 / 编辑员工")

with st.form("employee_form"):
    edit_id = st.text_input("员工ID（编辑时填写，新增留空）")
    name = st.text_input("姓名", placeholder="张三")
    position = st.text_input("岗位", placeholder="创意策划")
    industry_experience = st.text_area("行业经验", placeholder="3年短视频营销经验")
    content_style = st.text_input("内容风格", placeholder="幽默接地气，擅长玩梗")
    ai_assistant_type = st.selectbox("AI助手类型", EMPLOYEE_STYLE_TYPES)
    expertise = st.text_input("擅长领域（逗号分隔）", placeholder="搞笑, 剧情, 开箱")

    st.write("**自定义 Prompt 模板（可选）**")
    st.caption("可用变量: {{topic}} {{viral_model}} {{idea}}")
    idea_prompt_template = st.text_area(
        "创意生成 prompt 模板",
        placeholder="留空使用默认。示例：主题{{topic}}，参考爆款模型{{viral_model}}，生成符合我风格的创意",
        height=100,
    )
    script_prompt_template = st.text_area(
        "脚本生成 prompt 模板",
        placeholder="留空使用默认。示例：创意{{idea}}，写成我风格的分镜脚本",
        height=100,
    )

    if st.form_submit_button("保存"):
        if not name or not position:
            st.error("请填写姓名和岗位")
        else:
            profile = EmployeeProfile(
                id=edit_id or "",
                name=name,
                position=position,
                industry_experience=industry_experience.strip(),
                content_style=content_style or "通用",
                ai_assistant_type=ai_assistant_type,
                expertise=[x.strip() for x in expertise.split(",") if x.strip()],
                idea_prompt_template=idea_prompt_template.strip(),
                script_prompt_template=script_prompt_template.strip(),
            )
            store.save(profile)
            st.success("已保存")
            st.rerun()
