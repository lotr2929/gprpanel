@echo off  
chcp 65001 >nul  
title GPR Plant Database - Nightly Enrichment  
cd /d C:\_myProjects\_GPR\GPR-PlantDB\lai  
python enrich_all.py  
pause  
