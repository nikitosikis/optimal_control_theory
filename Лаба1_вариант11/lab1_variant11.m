%% Лабораторная работа 1. Статическая оптимизация. Вариант 11.
% Запуск: откройте файл в MATLAB и нажмите Run.
% Дополнительные пакеты MATLAB не требуются.
% Исходные данные: Задания1_6_ОУ 2026.pdf, задание 1, вариант 11.
% Методы: ТОУ_1.pdf, слайды 7-10.
clear; clc; close all;
format long g;
outDir = fullfile(fileparts(mfilename('fullpath')), 'results');
if ~exist(outDir, 'dir'), mkdir(outDir); end

%% 1.1. Без ограничений
H = [16 4; 4 12];
b = [1; 3];
J = @(z) 0.5*z.'*H*z + b.'*z - 10;
gradJ = @(z) H*z + b;
c = @(z) 3*z(1) - z(2)^2 + 1;
gradc = @(z) [3; -2*z(2)];
zFree = -(H\b);
JFree = J(zFree);
eigenH = sort(eig(H));
assert(all(eigenH > 0), 'Гессиан должен быть положительно определён.');
assert(norm(gradJ(zFree)) < 1e-12);
fprintf('Без ограничений: x = %.12f, u = %.12f, J = %.12f\n', ...
    zFree(1), zFree(2), JFree);

%% 1.2. Ограничение-равенство 3*x - u^2 + 1 = 0
% x = (u^2-1)/3. На границе J = phi(u).
% phi = (8*u^4 + 12*u^3 + 41*u^2 + 15*u - 85)/9.
% phi' = (32*u^3 + 36*u^2 + 82*u + 15)/9.
% phi'' = (96*(u+3/8)^2 + 137/2)/9 > 0 для любого u.
phiCoeffs = [8 12 41 15 -85]/9;
allRoots = roots([32 36 82 15]);
realRoots = real(allRoots(abs(imag(allRoots)) < 1e-10));
assert(numel(realRoots) == 1, 'Ожидается один действительный корень.');
uEq = realRoots(1);
zEq = [(uEq^2-1)/3; uEq];
lambdaEq = -(16*zEq(1) + 4*zEq(2) + 1)/3;
JEq = J(zEq);
HEq = H + [0 0; 0 -2*lambdaEq];
assert(abs(c(zEq)) < 1e-12);
assert(norm(gradJ(zEq) + lambdaEq*gradc(zEq)) < 1e-10);
assert(all(eig(HEq) > 0));
% Независимая проверка подстановки и численного минимума phi.
sampleU = linspace(-3,3,31);
for t = sampleU
    zp = [(t^2-1)/3; t];
    assert(abs(J(zp)-polyval(phiCoeffs,t)) < 1e-10);
end
[uCheck,~] = fminbnd(@(t) polyval(phiCoeffs,t), -3, 3, ...
    optimset('TolX',1e-12));
assert(abs(uCheck-uEq) < 1e-6);
fprintf('Равенство: x = %.12f, u = %.12f, lambda = %.12f, J = %.12f\n', ...
    zEq(1), zEq(2), lambdaEq, JEq);

%% 1.3. Ограничение-неравенство 3*x - u^2 + 1 <= 0
% Неактивная ветвь: lambda=0 даёт zFree, но c(zFree)=15/16>0.
% Активная ветвь: c=0 даёт найденную выше точку; lambdaEq>0.
% Глобальная достаточность: HEq>0, поэтому L(z,lambdaEq)>=L(zEq,lambdaEq).
% Для c(z)<=0: J(z)>=L(z,lambdaEq)>=L(zEq,lambdaEq)=J(zEq).
assert(c(zFree) > 0 && lambdaEq > 0);
zIneq = zEq;
lambdaIneq = lambdaEq;
JIneq = JEq;
fprintf('Неравенство: x = %.12f, u = %.12f, lambda = %.12f, J = %.12f\n', ...
    zIneq(1), zIneq(2), lambdaIneq, JIneq);

%% 2.1. Метод Ньютона-Рафсона для J1=J без ограничений
z0 = [0;0];
tol = 1e-6; % Общий критерий остановки: norm(gradJ(z_k),2) <= tol.
newton = iterateMethod(H,b,z0,tol,NaN,'newton');
assert(height(newton) == 2 && norm([newton.x(end);newton.u(end)]-zFree)<1e-12);
writetable(newton, fullfile(outDir,'newton.csv'));

%% 2.2. Метод наискорейшего спуска в обозначениях лекции
% Используется формула лекции с постоянным gamma, а не точный поиск шага.
% Сходимость: 0 < gamma < 2/lambda_max(H).
% Апериодический режим: 0 < gamma < 1/lambda_max(H).
% Колебательный режим: 1/lambda_max(H) < gamma < 2/lambda_max(H).
gammaAp = 0.05;
gammaOsc = 0.09;
aperiodic = iterateMethod(H,b,z0,tol,gammaAp,'gradient');
oscillatory = iterateMethod(H,b,z0,tol,gammaOsc,'gradient');
writetable(aperiodic, fullfile(outDir,'descent_005.csv'));
writetable(oscillatory, fullfile(outDir,'descent_009.csv'));
factorsAp = 1-gammaAp*eigenH;
factorsOsc = 1-gammaOsc*eigenH;
assert(all(factorsAp>0 & factorsAp<1));
assert(any(factorsOsc<0) && all(abs(factorsOsc)<1));
for cells = {aperiodic,oscillatory}
    T = cells{1};
    assert(T.grad_norm(end)<=tol && T.grad_norm(end-1)>tol);
    assert(all(diff(T.J)<=1e-12), 'Критерий должен убывать.');
end
fprintf('Собственные значения H: %.12f, %.12f\n', eigenH);
fprintf('Границы шага: 1/L = %.12f; 2/L = %.12f\n', ...
    1/eigenH(end),2/eigenH(end));
fprintf('gamma=0.05: %d итерации, норма градиента %.12e\n', ...
    height(aperiodic)-1,aperiodic.grad_norm(end));
fprintf('gamma=0.09: %d итераций, норма градиента %.12e\n', ...
    height(oscillatory)-1,oscillatory.grad_norm(end));

%% Графики
set(groot,'defaultAxesFontName','Arial','defaultTextFontName','Arial');
set(groot,'defaultAxesFontSize',12,'defaultLineLineWidth',1.5);
% Явные цвета сохраняют читаемость графиков при любой теме MATLAB.
set(groot,'defaultAxesColor','w','defaultAxesXColor','k','defaultAxesYColor','k', ...
    'defaultTextColor','k','defaultAxesGridColor',[.3 .3 .3], ...
    'defaultAxesGridAlpha',0.15,'defaultAxesMinorGridAlpha',0.08, ...
    'defaultLegendColor','w','defaultLegendTextColor','k', ...
    'defaultLegendEdgeColor',[.4 .4 .4]);
blue = [0.05 0.30 0.60]; orange = [0.85 0.32 0.10];

f = figure('Visible','off','Color','w','Position',[100 100 1100 650]);
tiledlayout(1,2,'Padding','compact','TileSpacing','compact');
nexttile; hold on;
ur = linspace(-0.85,0.65,500); xb = (ur.^2-1)/3;
hFeas = fill([-0.65 xb -0.65], [ur(1) ur ur(end)], ...
    [0.88 0.94 0.99],'EdgeColor','none');
[X,U] = meshgrid(linspace(-0.65,0.30,400),ur);
JJ = 8*X.^2+6*U.^2+4*X.*U+X+3*U-10;
[~,hContour] = contour(X,U,JJ,[-10.35 -10.25 -10.0 JEq -9.3 -8.8 -8.0], ...
    'LineColor',[0.5 0.5 0.5]);
hBound = plot(xb,ur,'Color',[0.40 0.20 0.55],'LineWidth',2);
hFree = plot(zFree(1),zFree(2),'o','MarkerSize',8, ...
    'MarkerFaceColor',blue,'Color',blue);
hEq = plot(zEq(1),zEq(2),'p','MarkerSize',13, ...
    'MarkerFaceColor',orange,'Color',orange);
xlim([-0.65 .30]); ylim([-.85 .65]); grid on;
xlabel('x'); ylabel('u'); title('Минимумы и допустимая область');
legend([hFeas hContour hBound hFree hEq], ...
    {'c(x,u) <= 0','Линии уровня J','c(x,u) = 0', ...
    'Без ограничений','С ограничениями'},'Location','northeast','FontSize',9);
nexttile; hold on;
us = linspace(-1.4,1.0,600);
plot(us,polyval(phiCoeffs,us),'Color',blue);
plot(uEq,JEq,'p','MarkerSize',13,'MarkerFaceColor',orange,'Color',orange);
xlabel('u'); ylabel('\phi(u)'); title('Критерий на границе ограничения'); grid on;
text(uEq+.07,JEq+.2,sprintf('u_* = %.6f\nJ_* = %.6f',uEq,JEq));
exportgraphics(f,fullfile(outDir,'constraints.png'),'Resolution',220,'BackgroundColor','white'); close(f);

f = figure('Visible','off','Color','w','Position',[100 100 1100 800]);
tiledlayout(2,2,'Padding','compact','TileSpacing','compact');
nexttile; plot(aperiodic.k,aperiodic.x,'o-','Color',blue,'MarkerSize',3); hold on;
plot(oscillatory.k,oscillatory.x,'s-','Color',orange,'MarkerSize',3);
yline(zFree(1),'k:'); xlabel('k'); ylabel('x_k'); grid on; title('Координата x');
legend('\gamma = 0.05','\gamma = 0.09','x_*','Location','northeast');
nexttile; plot(aperiodic.k,aperiodic.u,'o-','Color',blue,'MarkerSize',3); hold on;
plot(oscillatory.k,oscillatory.u,'s-','Color',orange,'MarkerSize',3);
yline(zFree(2),'k:'); xlabel('k'); ylabel('u_k'); grid on; title('Координата u');
nexttile; semilogy(aperiodic.k,aperiodic.grad_norm,'o-','Color',blue,'MarkerSize',3); hold on;
semilogy(oscillatory.k,oscillatory.grad_norm,'s-','Color',orange,'MarkerSize',3);
yline(tol,'k:'); xlabel('k'); ylabel('||grad J||_2'); grid on; title('Критерий остановки');
nexttile; semilogy(aperiodic.k,aperiodic.gap,'o-','Color',blue,'MarkerSize',3); hold on;
semilogy(oscillatory.k,oscillatory.gap,'s-','Color',orange,'MarkerSize',3);
xlabel('k'); ylabel('J(z_k) - J_*'); grid on; title('Убывание ошибки критерия');
exportgraphics(f,fullfile(outDir,'descent.png'),'Resolution',220,'BackgroundColor','white'); close(f);

f = figure('Visible','off','Color','w','Position',[100 100 850 650]); hold on;
[X,U] = meshgrid(linspace(-.12,.075,350),linspace(-.30,.035,350));
JJ = 8*X.^2+6*U.^2+4*X.*U+X+3*U-10;
contour(X,U,JJ,JFree+[.0003 .001 .003 .01 .03 .1 .2 .375], ...
    'LineColor',[.7 .7 .7]);
hAp = plot(aperiodic.x,aperiodic.u,'o-','Color',blue,'MarkerSize',4);
hOsc = plot(oscillatory.x,oscillatory.u,'s-','Color',orange,'MarkerSize',4);
hN = plot(newton.x,newton.u,'k--','LineWidth',1.4);
hS = plot(z0(1),z0(2),'ko','MarkerFaceColor','w','MarkerSize',8);
hEnd = plot(zFree(1),zFree(2),'kp','MarkerFaceColor','k','MarkerSize',11);
xlabel('x'); ylabel('u'); grid on; title('Траектории численного поиска');
legend([hAp hOsc hN hS hEnd],{'\gamma = 0.05','\gamma = 0.09', ...
    'Ньютон','Начальная точка','Минимум'},'Location','southeast');
exportgraphics(f,fullfile(outDir,'trajectories.png'),'Resolution',220,'BackgroundColor','white'); close(f);

%% Результаты для проверки и формирования отчёта
R = struct('variant',11,'H',H,'b',b,'z0',z0,'tolerance',tol, ...
    'z_free',zFree,'J_free',JFree,'constraint_at_free',c(zFree), ...
    'cubic_roots',[real(allRoots),imag(allRoots)],'z_equality',zEq, ...
    'J_equality',JEq,'lambda_equality',lambdaEq, ...
    'z_inequality',zIneq,'J_inequality',JIneq,'lambda_inequality',lambdaIneq, ...
    'lagrangian_hessian',HEq,'lagrangian_hessian_eigenvalues',sort(eig(HEq)), ...
    'eigenvalues_H',eigenH,'gamma_aperiodic',gammaAp,'gamma_oscillatory',gammaOsc, ...
    'factors_aperiodic',factorsAp,'factors_oscillatory',factorsOsc, ...
    'iterations_newton',height(newton)-1,'iterations_aperiodic',height(aperiodic)-1, ...
    'iterations_oscillatory',height(oscillatory)-1,'all_checks_passed',true);
fid = fopen(fullfile(outDir,'results.json'),'w','n','UTF-8');
assert(fid~=-1,'Не удалось создать results.json.');
fileCloser = onCleanup(@() fclose(fid));
fprintf(fid,'%s',jsonencode(R,'PrettyPrint',true));
clear fileCloser;
save(fullfile(outDir,'lab1_results.mat'),'R','newton','aperiodic','oscillatory');
disp('Все проверки пройдены. Графики, таблицы и результаты записаны в results.');

function T = iterateMethod(H,b,z0,tol,gamma,method)
    maxIter = 10000;
    zStar = -(H\b);
    z = z0;
    data = zeros(maxIter+1,6);
    for k = 0:maxIter
        g = H*z+b;
        e = z-zStar;
        data(k+1,:) = [k,z.',0.5*z.'*H*z+b.'*z-10,norm(g),0.5*e.'*H*e];
        if norm(g)<=tol, break; end
        if strcmp(method,'newton')
            z = z-(H\g);
        else
            z = z-gamma*g;
        end
    end
    assert(k<maxIter,'Метод не сошёлся за maxIter шагов.');
    T = array2table(data(1:k+1,:), ...
        'VariableNames',{'k','x','u','J','grad_norm','gap'});
end
