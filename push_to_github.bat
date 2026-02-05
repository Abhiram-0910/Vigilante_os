@echo off
echo ============================================
echo  VIBHISHAN: Pushing to GitHub (Abhiram-0910)
echo ============================================

git remote remove origin
git remote add origin https://github.com/Abhiram-0910/Vigilante_os.git

echo [1/3] Adding files...
git add .

echo [2/3] Committing changes...
git commit -m "Final Submission: Production Ready (Voice + Safe Logic)"

echo [3/3] Pushing to main...
git push -u origin main

echo ============================================
echo  Done! Visit: https://github.com/Abhiram-0910/Vigilante_os
echo ============================================
pause
